"""Engine interface: every analysis backend speaks this language."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Dict, List


@dataclass
class Finding:
    """One evidence-backed finding."""
    title: str
    evidence: str
    severity: str = "info"  # info | low | medium | high
    meta: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title": self.title,
            "evidence": self.evidence,
            "severity": self.severity,
            "meta": self.meta,
        }


@dataclass
class EngineResult:
    target: str
    engine: str
    findings: List[Finding] = field(default_factory=list)
    raw: Dict[str, Any] = field(default_factory=dict)
    warnings: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "target": self.target,
            "engine": self.engine,
            "findings": [f.to_dict() for f in self.findings],
            "raw": self.raw,
            "warnings": self.warnings,
        }


class Engine:
    """Base class for all ARGUS engines."""

    name = "base"

    def available(self) -> bool:
        """True when the engine's backend tooling is installed."""
        return True

    def missing_hint(self) -> str:
        return f"Engine '{self.name}' backend is not installed."

    def analyze(self, target: str, **options: Any) -> EngineResult:
        raise NotImplementedError
