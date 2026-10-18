"""Secrets engine: find exposed credentials in code.

Scans JavaScript bundles, APK strings, and binary strings for:
  - API keys, AWS keys, GitHub/Slack/Google tokens
  - JWTs, private keys, hardcoded passwords

Evidence is MASKED (first 4 chars + ****) — ARGUS reports leaks,
it never spreads them.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Dict, List, Tuple
from urllib.parse import urlparse

from . import web as webmod
from .base import Engine, EngineResult, Finding

PATTERNS: List[Tuple[str, re.Pattern, str]] = [
    ("AWS access key",
     re.compile(r"AKIA[0-9A-Z]{16}"), "high"),
    ("GitHub token",
     re.compile(r"gh[pousr]_[A-Za-z0-9]{36,}"), "high"),
    ("Google API key",
     re.compile(r"AIza[0-9A-Za-z\-_]{35}"), "high"),
    ("Slack token",
     re.compile(r"xox[baprs]-[A-Za-z0-9\-]{10,60}"), "high"),
    ("Private key block",
     re.compile(r"-----BEGIN (?:RSA )?PRIVATE KEY-----"), "high"),
    ("JWT",
     re.compile(r"eyJ[A-Za-z0-9\-_]{8,}\.eyJ[A-Za-z0-9\-_]{8,}\.[A-Za-z0-9\-_]{8,}"),
     "medium"),
    ("Generic API key",
     re.compile(r"(?i)(?:api[_-]?key|apikey|secret[_-]?key)\s*[:=]\s*"
                r"['\"][A-Za-z0-9\-_]{16,}['\"]"), "medium"),
    ("Hardcoded password",
     re.compile(r"(?i)password\s*[:=]\s*['\"][^'\"]{4,40}['\"]"), "medium"),
]


def _mask(secret: str) -> str:
    s = secret.strip().strip("'\"")
    return (s[:4] + "****" + s[-2:]) if len(s) > 8 else "****"


def _collect_texts(target: str) -> List[str]:
    """Gather scannable text from a URL or a file."""
    if target.startswith(("http://", "https://")):
        try:
            html = webmod._fetch(target)
        except Exception:
            return []
        blobs = [html]
        for src in webmod._scripts(html, target)[:10]:
            if urlparse(src).netloc == urlparse(target).netloc:
                try:
                    blobs.append(webmod._fetch(src, timeout=10))
                except Exception:
                    continue
        return blobs
    p = Path(target)
    if not p.exists() or p.stat().st_size > 20_000_000:
        return []
    try:
        return [p.read_bytes().decode("utf-8", errors="ignore")]
    except Exception:
        return []


class SecretsEngine(Engine):
    name = "secrets"

    def analyze(self, target: str, **options: Any) -> EngineResult:
        result = EngineResult(target=target, engine=self.name)
        hits: Dict[str, List[str]] = {}
        for blob in _collect_texts(target):
            for label, pat, _sev in PATTERNS:
                for m in pat.findall(blob):
                    s = m if isinstance(m, str) else m[0]
                    hits.setdefault(label, [])
                    masked = _mask(s)
                    if masked not in hits[label]:
                        hits[label].append(masked)
        if not hits:
            result.findings.append(Finding(
                "No exposed secrets found",
                "Scanned JS/APK/binary text against 8 credential patterns.",
                meta={"patterns": [label for label, _, _ in PATTERNS]},
            ))
            return result
        sev_rank = {"high": 0, "medium": 1}
        for label, pat, sev in sorted(PATTERNS, key=lambda x: sev_rank[x[2]]):
            if label in hits:
                result.findings.append(Finding(
                    f"⚠️ {label} exposed ({len(hits[label])})",
                    "Masked samples: " + ", ".join(hits[label][:5]) +
                    " — rotate these credentials immediately.",
                    severity=sev,
                    meta={"count": len(hits[label])},
                ))
        result.raw = {"hit_types": sorted(hits)}
        return result
