"""Web engine: X-ray any website.

Fetches the page, then extracts:
  - tech-stack fingerprints (frameworks, CMS, analytics)
  - JavaScript bundles (first-party vs third-party)
  - API endpoints called from client-side code
  - trackers / third-party beacons
  - forms and where they submit

Pure Python, no browser needed. This engine is fully working in v0.1.
"""

from __future__ import annotations

import re
from typing import Any, Dict, List, Set
from urllib.parse import urljoin, urlparse

import requests

from .base import Engine, EngineResult, Finding

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/120.0 Safari/537.36"
    )
}

# --- fingerprint databases -------------------------------------------------

TECH_MARKERS: Dict[str, List[str]] = {
    "Next.js": ["__NEXT_DATA__", "_next/static"],
    "React": ["react-dom", "__REACT_DEVTOOLS_GLOBAL_HOOK__", "data-reactroot"],
    "Vue": ["__VUE__", "data-v-", "vue.runtime"],
    "Angular": ["ng-version", "angular.js", "_ngcontent"],
    "WordPress": ["wp-content", "wp-includes", "wp-json"],
    "Shopify": ["cdn.shopify.com", "Shopify.theme"],
    "Wix": ["wixstatic.com", "wix.com"],
    "Tailwind CSS": ["tailwind"],
    "Bootstrap": ["bootstrap"],
    "jQuery": ["jquery"],
    "Google Analytics": ["googletagmanager.com", "google-analytics.com"],
    "Cloudflare": ["cloudflare"],
}

TRACKER_DOMAINS = [
    "googletagmanager.com",
    "google-analytics.com",
    "facebook.net",
    "connect.facebook.net",
    "hotjar.com",
    "fullstory.com",
    "segment.io",
    "mixpanel.com",
    "amplitude.com",
    "intercom.io",
    "doubleclick.net",
    "googlesyndication.com",
]

ENDPOINT_PATTERNS = [
    re.compile(r"""fetch\(\s*['"`]([^'"`]+)['"`]"""),
    re.compile(r"""axios\.(?:get|post|put|delete|patch)\(\s*['"`]([^'"`]+)['"`]"""),
    re.compile(r"""\$\.(?:get|post|ajax)\(\s*['"`]([^'"`]+)['"`]"""),
    re.compile(r"""['"`](https?://[^'"`\s]{4,120})['"`]"""),
    re.compile(r"""['"`](/(?:api|v\d|graphql|rest)[^'"`\s]*)['"`]"""),
]

SCRIPT_SRC = re.compile(r"""<script[^>]+src=['"]([^'"]+)['"]""", re.IGNORECASE)
FORM_ACTION = re.compile(r"""<form[^>]+action=['"]([^'"]*)['"]""", re.IGNORECASE)
META_GENERATOR = re.compile(
    r"""<meta[^>]+name=['"]generator['"][^>]+content=['"]([^'"]+)['"]""",
    re.IGNORECASE,
)


def _fetch(url: str, timeout: int = 15) -> str:
    resp = requests.get(url, headers=HEADERS, timeout=timeout)
    resp.raise_for_status()
    return resp.text


def _scripts(html: str, base: str) -> List[str]:
    return [urljoin(base, s) for s in SCRIPT_SRC.findall(html)]


def _tech_stack(html: str) -> List[str]:
    found = [name for name, marks in TECH_MARKERS.items()
             if any(m.lower() in html.lower() for m in marks)]
    gen = META_GENERATOR.search(html)
    if gen:
        g = gen.group(1)
        named = [n for n in TECH_MARKERS if n.lower() in g.lower()]
        for n in named:
            if n not in found:
                found.append(n)
        if not named and g not in found:
            found.append(f"generator:{g}")
    return found


def _trackers(scripts: List[str]) -> List[str]:
    hits: Set[str] = set()
    for src in scripts:
        host = urlparse(src).netloc.lower()
        for t in TRACKER_DOMAINS:
            if t in host:
                hits.add(t)
    return sorted(hits)


def _endpoints(js_blobs: List[str]) -> List[str]:
    found: Set[str] = set()
    for blob in js_blobs:
        for pat in ENDPOINT_PATTERNS:
            for m in pat.findall(blob):
                m = m.strip()
                if len(m) > 3 and not m.startswith("data:"):
                    found.add(m)
    return sorted(found)[:200]


def _forms(html: str, base: str) -> List[str]:
    return [urljoin(base, a or base) for a in FORM_ACTION.findall(html)]


class WebEngine(Engine):
    name = "web"

    def analyze(self, target: str, **options: Any) -> EngineResult:
        deep = bool(options.get("deep", False))
        result = EngineResult(target=target, engine=self.name)

        try:
            html = _fetch(target)
        except Exception as exc:  # network failure -> honest finding, not a crash
            result.warnings.append(f"fetch failed: {exc}")
            return result

        scripts = _scripts(html, target)
        tech = _tech_stack(html)
        trackers = _trackers(scripts)
        forms = _forms(html, target)

        first_party = [s for s in scripts
                       if urlparse(s).netloc == urlparse(target).netloc]
        third_party = [s for s in scripts
                       if urlparse(s).netloc != urlparse(target).netloc]

        endpoints: List[str] = []
        if deep:
            blobs: List[str] = []
            for src in first_party[:10]:  # cap: don't hammer the target
                try:
                    blobs.append(_fetch(src, timeout=10))
                except Exception:
                    continue
            endpoints = _endpoints(blobs + [html])

        if tech:
            result.findings.append(Finding(
                "Tech stack detected",
                f"Markers found: {', '.join(tech)}",
                meta={"tech": tech},
            ))
        result.findings.append(Finding(
            "JavaScript bundles",
            f"{len(scripts)} scripts ({len(first_party)} first-party, "
            f"{len(third_party)} third-party)",
            meta={"first_party": first_party[:20],
                  "third_party": third_party[:20]},
        ))
        if trackers:
            result.findings.append(Finding(
                "Trackers detected",
                f"Third-party beacons: {', '.join(trackers)}",
                severity="low",
                meta={"trackers": trackers},
            ))
        if forms:
            result.findings.append(Finding(
                "Forms found",
                f"{len(forms)} form(s) submit to: {', '.join(forms[:5])}",
                meta={"actions": forms},
            ))
        if endpoints:
            result.findings.append(Finding(
                "API endpoints (from client code)",
                f"{len(endpoints)} candidate endpoints extracted",
                meta={"endpoints": endpoints},
            ))

        result.raw = {
            "tech": tech,
            "scripts_total": len(scripts),
            "trackers": trackers,
            "forms": forms,
            "endpoints": endpoints,
        }
        return result


def analyze_website(url: str, deep: bool = False) -> Dict[str, Any]:
    """Convenience wrapper used by CLI / MCP / tests."""
    return WebEngine().analyze(url, deep=deep).to_dict()
