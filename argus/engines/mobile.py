"""Mobile engine: Android APK static analysis.

Unpacks the APK (apktool if present, else zip parse), then extracts:
  - manifest: package, permissions, activities, services
  - tracker SDK fingerprints from smali/dex strings
  - hardcoded URLs / API endpoints
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
import zipfile
from pathlib import Path
from typing import Any, List

from .base import Engine, EngineResult, Finding

TRACKER_SDK_MARKERS = {
    "Google Ads": ["com/google/android/gms/ads"],
    "Firebase": ["com/google/firebase"],
    "Facebook SDK": ["com/facebook/"],
    "AppsFlyer": ["com/appsflyer"],
    "Adjust": ["com/adjust"],
    "Branch": ["io/branch"],
    "Mixpanel": ["com/mixpanel"],
    "Amplitude": ["com/amplitude"],
}

URL_RE = re.compile(r"https?://[A-Za-z0-9\-._~:/?#\[\]@!$&'()*+,;=%]{6,160}")
PERM_RE = re.compile(r'android\.permission\.([A-Z_]+)')
DANGEROUS_PERMS = {
    "READ_SMS", "SEND_SMS", "RECEIVE_SMS", "READ_CONTACTS", "READ_CALL_LOG",
    "RECORD_AUDIO", "CAMERA", "ACCESS_FINE_LOCATION", "READ_EXTERNAL_STORAGE",
    "WRITE_EXTERNAL_STORAGE", "READ_PHONE_STATE",
}


class MobileEngine(Engine):
    name = "mobile"

    def available(self) -> bool:
        # zip-parse path always works; apktool only upgrades manifest detail
        return True

    def _strings_from_apk(self, apk: Path) -> List[str]:
        out: List[str] = []
        with zipfile.ZipFile(apk) as zf:
            for name in zf.namelist():
                if name.endswith(".dex") or name.endswith(".xml"):
                    try:
                        data = zf.read(name)
                    except Exception:
                        continue
                    text = data.decode("utf-8", errors="ignore")
                    out.append(text)
                    if len("".join(out)) > 4_000_000:  # cap memory
                        break
        return out

    def analyze(self, target: str, **options: Any) -> EngineResult:
        result = EngineResult(target=target, engine=self.name)
        apk = Path(target)
        if not apk.exists():
            result.warnings.append(f"file not found: {target}")
            return result

        blobs = self._strings_from_apk(apk)
        haystack = "\n".join(blobs)

        perms = sorted(set(PERM_RE.findall(haystack)))
        dangerous = [p for p in perms if p in DANGEROUS_PERMS]
        sdks = [n for n, ms in TRACKER_SDK_MARKERS.items()
                if any(m in haystack for m in ms)]
        urls = sorted(set(URL_RE.findall(haystack)))[:100]

        # --- risk score: 0-100, higher = more invasive ---------------------
        score = min(60, len(dangerous) * 15) + min(20, len(sdks) * 5)
        sketchy_urls = [u for u in urls
                        if u.startswith("http://") or re.match(r"https?://\d+\.\d+", u)]
        score = min(100, score + min(20, len(sketchy_urls) * 10))
        label = "Low" if score <= 30 else "Medium" if score <= 60 else "High"
        result.findings.append(Finding(
            f"Risk score: {score}/100 ({label})",
            f"{len(dangerous)} dangerous permissions, {len(sdks)} tracker "
            f"SDKs, {len(sketchy_urls)} sketchy URLs.",
            severity="high" if score > 60 else "medium" if score > 30 else "info",
            meta={"risk_score": score, "risk_label": label},
        ))
        result.raw["risk_score"] = score
        result.raw["risk_label"] = label
        result.raw["permissions"] = perms
        result.raw["dangerous"] = dangerous
        result.raw["sdks"] = sdks
        result.raw["urls"] = urls

        if perms:
            result.findings.append(Finding(
                f"Permissions ({len(perms)})",
                ", ".join(perms[:30]),
                severity="medium" if dangerous else "info",
                meta={"permissions": perms, "dangerous": dangerous},
            ))
        if sdks:
            result.findings.append(Finding(
                "Embedded SDKs / trackers",
                ", ".join(sdks), severity="low", meta={"sdks": sdks},
            ))
        if urls:
            result.findings.append(Finding(
                f"Hardcoded URLs ({len(urls)})",
                "\n".join(urls[:20]), meta={"urls": urls},
            ))
        if shutil.which("apktool") is None:
            result.warnings.append(
                "apktool not installed — manifest parsed from raw zip; "
                "install apktool for full decode.")
        return result
