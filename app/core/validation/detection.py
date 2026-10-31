"""Versionserkennung: passt eine Datei zum Guide-Stand (CH 2.0) oder zur NeTEx-1.10-Lieferung?

Mehrere Hinweise werden gesammelt und gewichtet (Namensraum, `version`-Attribut,
`schemaLocation`, Kommentare, Dateiname, Struktur). Das Wurzelattribut entscheidet nie allein:
Guide-Beispiele tragen teils `version="1.09"`. Jeder Hinweis steht mit Begründung im Ergebnis.

Entscheidung: Gewinnt eine Version mit mindestens zwei verschiedenen Hinweisen und zwei Punkten
Vorsprung, gilt sie als erkannt (`detected`). Gibt es Hinweise, aber keinen klaren Sieger, ist das
Ergebnis `ambiguous`; ohne verwertbare Hinweise (oder ohne NeTEx-Namensraum) `unknown`.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from enum import StrEnum
from pathlib import PurePosixPath
from typing import Final

from app.core.messages import MessageKey, ParamValue
from app.core.reader.xml_reader import ParsedFile

NETEX_NAMESPACE: Final = "http://www.netex.org.uk/netex"
_SCHEMA_LOCATION_KEY: Final = "{http://www.w3.org/2001/XMLSchema-instance}schemaLocation"
_VERSION_20 = re.compile(r"^2\.\d+")
_LOCATION_110 = re.compile(r"/schema/1\.10(/|$)")
_LOCATION_20 = re.compile(r"/schema/2\.\d+(/|$)")
_GUIDE_LOCATION = re.compile(r"xsd/xsd/NeTEx_publication\.xsd$")
_COMMENT_PROFILE = re.compile(r"Profile:\s*([A-Za-z0-9_.-]{1,40})")
_FILE_TYPES: Final = ("NETWORK_OFFER", "SITE_OFFER", "INTERCHANGE")
_MAX_COMMENTS: Final = 10
_MIN_SIGNALS: Final = 2
_MIN_LEAD: Final = 2
_MAX_SHOWN: Final = 200

# Gewichte der Hinweise (Punkte)
_STRONG: Final = 2
_WEAK: Final = 1


class DetectionStatus(StrEnum):
    """Ergebnis der Versionserkennung."""

    DETECTED = "detected"
    AMBIGUOUS = "ambiguous"
    UNKNOWN = "unknown"


class ProfileVersion(StrEnum):
    """Erkennbare Versionen."""

    CH_2_0 = "ch_2_0"
    """CH-Profil 2.0 (Entwurf, NeTEx 2.1): der Guide-Stand, gegen den geprüft wird."""
    NETEX_1_10 = "netex_1_10"
    """NeTEx 1.10 (Lieferung 2027): wird nicht gegen 2.0 geprüft."""


class Evidence(StrEnum):
    """Wofür ein Hinweis spricht."""

    CH_2_0 = "ch_2_0"
    NETEX_1_10 = "netex_1_10"
    NEUTRAL = "neutral"


@dataclass(frozen=True)
class Reason:
    """Ein Hinweis mit Begründung (Übersetzungsschlüssel und Parameter)."""

    evidence: Evidence
    key: MessageKey
    params: dict[str, ParamValue]
    points: int = 0


@dataclass(frozen=True)
class VersionDetection:
    """Ergebnis für eine Datei: Status, erkannte Version (nur bei `detected`) und Begründung."""

    status: DetectionStatus
    profile: ProfileVersion | None
    reasons: tuple[Reason, ...]

    @property
    def checkable(self) -> bool:
        """Nur erkanntes CH 2.0 wird gegen den Guide-Stand geprüft."""
        return self.status is DetectionStatus.DETECTED and self.profile is ProfileVersion.CH_2_0

    @property
    def forceable(self) -> bool:
        """Mehrdeutige oder unbekannte Version: Prüfung als CH 2.0 nur auf ausdrücklichen Wunsch.

        Eine erkannte andere Version (z. B. 1.10) lässt sich nie erzwingen.
        """
        return self.status in (DetectionStatus.AMBIGUOUS, DetectionStatus.UNKNOWN)


def _shown(value: str) -> str:
    return value[:_MAX_SHOWN]


def _version_reason(version: str | None) -> Reason:
    if version is None:
        return Reason(Evidence.NEUTRAL, MessageKey.VERSION_ATTRIBUTE_MISSING, {})
    params: dict[str, ParamValue] = {"version": _shown(version)}
    if version.startswith("1.10"):
        return Reason(Evidence.NETEX_1_10, MessageKey.VERSION_ATTRIBUTE_110, params, _STRONG)
    if _VERSION_20.match(version):
        return Reason(Evidence.CH_2_0, MessageKey.VERSION_ATTRIBUTE_20, params, _STRONG)
    return Reason(Evidence.NEUTRAL, MessageKey.VERSION_ATTRIBUTE_OTHER, params)


def _schema_location_reason(location: str | None) -> Reason | None:
    if location is None:
        return None
    params: dict[str, ParamValue] = {"location": _shown(location)}
    if _LOCATION_110.search(location):
        return Reason(Evidence.NETEX_1_10, MessageKey.VERSION_SCHEMA_LOCATION_110, params, _STRONG)
    if _LOCATION_20.search(location):
        return Reason(Evidence.CH_2_0, MessageKey.VERSION_SCHEMA_LOCATION_20, params, _STRONG)
    if _GUIDE_LOCATION.search(location.strip()):
        return Reason(Evidence.CH_2_0, MessageKey.VERSION_SCHEMA_LOCATION_GUIDE, params, _WEAK)
    return Reason(Evidence.NEUTRAL, MessageKey.VERSION_SCHEMA_LOCATION_OTHER, params)


def _comment_reasons(parsed: ParsedFile) -> list[Reason]:
    reasons = []
    for comment in parsed.comments[:_MAX_COMMENTS]:
        match = _COMMENT_PROFILE.search(comment.text)
        if match:
            reasons.append(
                Reason(
                    Evidence.NETEX_1_10,
                    MessageKey.VERSION_COMMENT_PROFILE,
                    {"profile": match.group(1)},
                    _WEAK,
                )
            )
    return reasons


def _file_name_reason(file_name: str) -> Reason | None:
    base = PurePosixPath(file_name).name.upper()
    for file_type in _FILE_TYPES:
        if file_type in base:
            return Reason(
                Evidence.CH_2_0, MessageKey.VERSION_FILE_NAME_TYPE, {"type": file_type}, _WEAK
            )
    return None


def _structure_reasons(parsed: ParsedFile) -> list[Reason]:
    names = {element.name for element in parsed.elements}
    reasons = []
    if "ServiceJourneyPattern" in names and "TimeDemandType" in names:
        reasons.append(Reason(Evidence.CH_2_0, MessageKey.VERSION_STRUCTURE_PATTERN, {}, _STRONG))
    by_index = {element.index: element for element in parsed.elements}
    has_calls = any(
        element.name == "calls"
        and element.parent is not None
        and by_index[element.parent].name == "ServiceJourney"
        for element in parsed.elements
    )
    if has_calls:
        # Schwach: Das CH-Profil 2.0 verbietet `calls`, sie kommen aber auch in fehlerhaften
        # 2.0-Dateien vor (Kernregel CH-SJ-13); sie dürfen eine klare 2.0-Datei nicht kippen.
        reasons.append(Reason(Evidence.NETEX_1_10, MessageKey.VERSION_STRUCTURE_CALLS, {}, _WEAK))
    return reasons


def detect_version(parsed: ParsedFile) -> VersionDetection:
    """Erkennt die Version einer eingelesenen Datei; nicht lesbare Dateien sind `unknown`."""
    if not parsed.elements:
        return VersionDetection(DetectionStatus.UNKNOWN, None, ())
    root = parsed.elements[0]
    if root.namespace != NETEX_NAMESPACE:
        reason = Reason(
            Evidence.NEUTRAL, MessageKey.VERSION_NOT_NETEX, {"namespace": root.namespace or ""}
        )
        return VersionDetection(DetectionStatus.UNKNOWN, None, (reason,))
    reasons = [
        Reason(Evidence.NEUTRAL, MessageKey.VERSION_NAMESPACE, {"namespace": NETEX_NAMESPACE}),
        _version_reason(root.attributes.get("version")),
    ]
    location = _schema_location_reason(root.attributes.get(_SCHEMA_LOCATION_KEY))
    if location is not None:
        reasons.append(location)
    reasons.extend(_comment_reasons(parsed))
    name_reason = _file_name_reason(parsed.name)
    if name_reason is not None:
        reasons.append(name_reason)
    reasons.extend(_structure_reasons(parsed))
    return _decide(tuple(reasons))


def _decide(reasons: tuple[Reason, ...]) -> VersionDetection:
    scores = {Evidence.CH_2_0: 0, Evidence.NETEX_1_10: 0}
    signals = {Evidence.CH_2_0: 0, Evidence.NETEX_1_10: 0}
    for reason in reasons:
        if reason.evidence is not Evidence.NEUTRAL and reason.points:
            scores[reason.evidence] += reason.points
            signals[reason.evidence] += 1
    winner = max(scores, key=lambda evidence: scores[evidence])
    loser = Evidence.NETEX_1_10 if winner is Evidence.CH_2_0 else Evidence.CH_2_0
    if scores[winner] == 0:
        return VersionDetection(DetectionStatus.UNKNOWN, None, reasons)
    clear = signals[winner] >= _MIN_SIGNALS and scores[winner] >= scores[loser] + _MIN_LEAD
    if not clear:
        return VersionDetection(DetectionStatus.AMBIGUOUS, None, reasons)
    profile = ProfileVersion.CH_2_0 if winner is Evidence.CH_2_0 else ProfileVersion.NETEX_1_10
    return VersionDetection(DetectionStatus.DETECTED, profile, reasons)
