"""Liste der Prüfschritte mit Stand der Umsetzung und Quelle.

Die Hilfeseite zeigt daraus die durchgeführten und die nicht durchgeführten Prüfungen.
Jeder Schritt braucht in jeder Sprachdatei `check.<id>.title` und `check.<id>.description`;
ein Test prüft das.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from app.core.guide.layout import GENERAL_RULES_FILE, TEMPLATES_DIR, XSD_MAIN_FILE


class CheckStatus(StrEnum):
    """Stand eines Prüfschritts."""

    PERFORMED = "performed"
    NOT_IMPLEMENTED = "not_implemented"
    """In der ersten Ausbaustufe geplant, aber noch nicht umgesetzt."""
    DEFERRED = "deferred"
    """Nicht in der ersten Ausbaustufe; kommt später."""


@dataclass(frozen=True)
class CheckStep:
    """Ein Prüfschritt mit Kennung, Stand und Quellen (Pfade im Guide-Klon)."""

    id: str
    status: CheckStatus
    sources: tuple[str, ...] = ()


CHECK_STEPS: Final = (
    CheckStep("xml_syntax", CheckStatus.PERFORMED),
    CheckStep("references", CheckStatus.NOT_IMPLEMENTED),
    CheckStep("xsd", CheckStatus.NOT_IMPLEMENTED, (str(XSD_MAIN_FILE),)),
    CheckStep("general_rules", CheckStatus.NOT_IMPLEMENTED, (str(GENERAL_RULES_FILE),)),
    CheckStep(
        "ch_core_rules",
        CheckStatus.NOT_IMPLEMENTED,
        tuple(
            f"{TEMPLATES_DIR}/{name}"
            for name in ("ServiceJourney.xml", "ServiceJourneyPattern.xml", "TimeDemandType.xml")
        ),
    ),
    CheckStep("ch_profile_rules", CheckStatus.DEFERRED, (str(TEMPLATES_DIR),)),
)
