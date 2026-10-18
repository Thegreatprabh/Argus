"""Binary engine: static analysis of executables via radare2.

REA does not wrap radare2 — this is one of ARGUS's edges.
Falls back to `rabin2`/readelf-style info when r2pipe is missing.
"""

from __future__ import annotations

import shutil
import subprocess
from typing import Any

from .base import Engine, EngineResult, Finding


class BinaryEngine(Engine):
    name = "binary"

    def available(self) -> bool:
        return shutil.which("r2") is not None or shutil.which("rabin2") is not None

    def missing_hint(self) -> str:
        return ("radare2 not found. Install it: https://rada.re/n/radare2.html "
                "(e.g. `sudo apt install radare2`).")

    def _rabin2_info(self, target: str) -> str:
        out = subprocess.run(
            ["rabin2", "-I", target], capture_output=True, text=True, timeout=60
        )
        return out.stdout or out.stderr

    def _r2_strings(self, target: str, limit: int = 40) -> list[str]:
        try:
            import r2pipe  # type: ignore
        except ImportError:
            return []
        r2 = r2pipe.open(target, flags=["-2"])
        try:
            r2.cmd("aaa")
            strings = r2.cmdj("izj") or []
            interesting = [
                s.get("string", "") for s in strings
                if len(s.get("string", "")) > 6
            ]
            return interesting[:limit]
        finally:
            r2.quit()

    def analyze(self, target: str, **options: Any) -> EngineResult:
        result = EngineResult(target=target, engine=self.name)
        if not self.available():
            result.warnings.append(self.missing_hint())
            return result
        try:
            info = self._rabin2_info(target)
        except Exception as exc:
            result.warnings.append(f"rabin2 failed: {exc}")
            return result
        result.findings.append(Finding(
            "Binary info", info.strip()[:2000], meta={"raw_info": info[:4000]},
        ))
        strings = self._r2_strings(target)
        if strings:
            result.findings.append(Finding(
                f"Interesting strings ({len(strings)})",
                "\n".join(strings[:20]),
                meta={"strings": strings},
            ))
        else:
            result.warnings.append(
                "r2pipe not installed — deep string/function analysis skipped "
                "(`pip install r2pipe`).")
        return result
