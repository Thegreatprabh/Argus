"""Dynamic engine: runtime inspection via Frida.

REA does not wrap Frida — this is ARGUS's biggest edge:
static analysis tells you what code *says*; Frida shows what it *does*.
"""

from __future__ import annotations

import shutil
from typing import Any, List

from .base import Engine, EngineResult, Finding


class DynamicEngine(Engine):
    name = "dynamic"

    def available(self) -> bool:
        try:
            import frida  # type: ignore  # noqa: F401
            return True
        except ImportError:
            return shutil.which("frida-ps") is not None

    def missing_hint(self) -> str:
        return ("Frida not found. Install: `pip install frida-tools`. "
                "See https://frida.re/docs/installation/")

    def list_processes(self) -> List[str]:
        try:
            import frida  # type: ignore
        except ImportError:
            return []
        try:
            dev = frida.get_local_device()
            return [f"{p.pid}: {p.name}" for p in dev.enumerate_processes()][:50]
        except Exception:
            return []

    def analyze(self, target: str, **options: Any) -> EngineResult:
        result = EngineResult(target=target, engine=self.name)
        if not self.available():
            result.warnings.append(self.missing_hint())
            return result
        mode = options.get("mode", "ps")
        if mode == "ps":
            procs = self.list_processes()
            result.findings.append(Finding(
                f"Local processes ({len(procs)})",
                "\n".join(procs[:25]),
                meta={"processes": procs},
            ))
            result.warnings.append(
                "Attach mode (`mode='attach'`, target=process name) hooks "
                "API calls at runtime — see docs/ARCHITECTURE.md.")
        return result
