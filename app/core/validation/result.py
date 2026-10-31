"""Ergebnis einer Validierung: welche Schritte und Dateien geprüft wurden und was nicht."""

from __future__ import annotations

from dataclasses import dataclass

from app.core.messages import Issue


@dataclass(frozen=True)
class StepOutcome:
    """Ein Prüfschritt: durchgeführt oder, mit Grund, nicht durchgeführt."""

    step_id: str
    performed: bool
    reason: Issue | None = None


@dataclass(frozen=True)
class FileOutcome:
    """Eine Datei: geprüft oder, mit Grund, nicht geprüft (z. B. andere Version).

    `forced`: auf ausdrücklichen Wunsch als CH 2.0 geprüft, obwohl die Version nicht erkannt war.
    """

    file_id: int
    checked: bool
    reason: Issue | None = None
    forced: bool = False


@dataclass(frozen=True)
class ValidationSummary:
    """Zusammenfassung einer Validierung eines Datensatzes."""

    guide_commit: str | None
    steps: tuple[StepOutcome, ...]
    files: tuple[FileOutcome, ...]

    @property
    def forced(self) -> bool:
        """`True`, wenn mindestens eine Datei auf Wunsch als CH 2.0 geprüft wurde."""
        return any(outcome.forced for outcome in self.files)
