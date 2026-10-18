"""Firmware engine: firmware image analysis via Binwalk.

Extracts embedded signatures (filesystems, kernels, bootloaders)
from firmware blobs — routers, IoT, Android boot images.
"""

from __future__ import annotations

import re
import shutil
import subprocess
from pathlib import Path
from typing import Any, List

from .base import Engine, EngineResult, Finding

SIG_RE = re.compile(r"^\s*(\d+)\s+0x[0-9A-Fa-f]+\s+(.+?)\s*$")


class FirmwareEngine(Engine):
    name = "firmware"

    def available(self) -> bool:
        return shutil.which("binwalk") is not None

    def missing_hint(self) -> str:
        return ("binwalk not found. Install: `sudo apt install binwalk` "
                "(Linux) or `pkg install binwalk` (Termux).")

    def _run(self, target: str) -> str:
        out = subprocess.run(
            ["binwalk", target], capture_output=True, text=True, timeout=300)
        return out.stdout or out.stderr

    def _parse(self, text: str) -> List[tuple[str, str]]:
        sigs = []
        for line in text.splitlines():
            m = SIG_RE.match(line)
            if m and "DECIMAL" not in line.upper():
                sigs.append((m.group(1), m.group(2).strip()))
        return sigs

    def analyze(self, target: str, **options: Any) -> EngineResult:
        result = EngineResult(target=target, engine=self.name)
        if not Path(target).exists():
            result.warnings.append(f"file not found: {target}")
            return result
        if not self.available():
            result.warnings.append(self.missing_hint())
            return result
        try:
            raw = self._run(target)
        except Exception as exc:
            result.warnings.append(f"binwalk failed: {exc}")
            return result
        sigs = self._parse(raw)
        if sigs:
            interesting = [s for _, s in sigs
                           if any(k in s.lower() for k in
                                   ("squashfs", "cramfs", "jffs2", "kernel",
                                    "u-boot", "gzip", "lzma", "filesystem"))]
            result.findings.append(Finding(
                f"Embedded signatures ({len(sigs)})",
                "\n".join(f"@{off}: {desc}" for off, desc in sigs[:30]),
                severity="medium" if interesting else "info",
                meta={"signatures": [list(s) for s in sigs[:50]]},
            ))
        else:
            result.warnings.append("no signatures recognized in this file.")
        result.raw = {"binwalk_output": raw[:6000]}
        return result
