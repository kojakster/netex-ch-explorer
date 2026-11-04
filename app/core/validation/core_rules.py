"""Schweizer Kernregeln für den Fahrplan (CH 2.0): Pflichtelemente, Verbote und erlaubte Werte.

Die Regeln sind selbst hergeleitet aus den Vorlagen des Guides (`src/templates/*.xml`); Herleitung,
Belege und Entscheide: docs/core-rules.md und docs/decisions.md („Kernregeln Phase 4“). Jede Regel
trägt Kennung, Quelle (Vorlage und Zeilen im geprüften Guide-Commit) und Schweregrad. Die Liste
`CORE_RULES` ist erweiterbar: eine neue Regel ist ein neuer Eintrag, kein neuer Code.

Nicht umgesetzt (Entscheide vom 31.10.2026): CH-SJP-08 und CH-SJ-16.

Eine Rumpf-Fahrt (`ServiceJourney` ohne `ServiceJourneyPatternRef`, nur mit `privateCodes`, z. B. in
`INTERCHANGE`-Dateien) unterliegt den Fahrt-Regeln nicht; sie ergibt einen Hinweis.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Final, TypedDict, Unpack

from app.core.diagnostics import Diagnostic, DiagnosticCategory
from app.core.guide.layout import CHAPTER_JOURNEY_PARTS, CHAPTER_TIMETABLE, TEMPLATES_DIR
from app.core.index.dataset_index import DatasetIndex, ElementRow
from app.core.messages import MessageKey, ParamValue, Severity

STEP_ID: Final = "ch_core_rules"
JOURNEY: Final = "ServiceJourney"
PATTERN_REF: Final = "ServiceJourneyPatternRef"
PRIVATE_CODES: Final = "privateCodes"

type Path = tuple[str, ...]


class RuleKind(StrEnum):
    """Art einer Regel."""

    REQUIRED = "required"
    """Mindestens ein Element unter dem Pfad (Pflicht, wenn das Elternelement vorhanden ist)."""
    EXACTLY_ONE = "exactly_one"
    """Genau ein Element unter dem Pfad."""
    FORBIDDEN = "forbidden"
    """Kein Element unter dem Pfad (optional nur mit bestimmtem Text)."""
    VALUE = "value"
    """Text bzw. Attribut `ref` des Elements ist einer der erlaubten Werte."""
    EXPECTED = "expected"
    """Wie `REQUIRED`, aber nur „expected“ im Guide: fehlt es, gibt es einen Hinweis."""


@dataclass(frozen=True)
class CoreRule:
    """Eine Kernregel.

    Attributes:
        id: Kennung (`CH-SJ-01`).
        kind: Art der Regel.
        context: Elementname, für den die Regel gilt (jedes solche Element).
        targets: Pfade unter dem Kontextelement (Kindelemente, Schritt für Schritt). Mehrere Pfade
            sind Alternativen (Auswahl): ein vorhandener genügt.
        severity: Schweregrad bei Verstoss.
        template: Vorlage im Guide (Dateiname unter `src/templates/`).
        lines: Zeilen in der Vorlage (Text, z. B. `13-19`).
        allowed: Erlaubte Werte (nur `VALUE`).
        attribute: Attribut, das geprüft wird (nur `VALUE`); sonst der Text des Elements.
        text_equals: Nur Elemente mit diesem Text zählen (nur `FORBIDDEN`).
        chapter: Kapitel des Guides, das die Regel beschreibt (Pfad im Guide-Klon).
    """

    id: str
    kind: RuleKind
    context: str
    targets: tuple[Path, ...]
    severity: Severity
    template: str
    lines: str
    allowed: tuple[str, ...] = ()
    attribute: str | None = None
    text_equals: str | None = None
    chapter: str = str(CHAPTER_TIMETABLE)

    @property
    def source(self) -> str:
        """Quelle als Text: Vorlage und Zeilen."""
        return f"{TEMPLATES_DIR.name}/{self.template} Z. {self.lines}"

    @property
    def path_text(self) -> str:
        """Pfad(e) als Text; Alternativen mit ` | ` getrennt."""
        return " | ".join("/".join(path) for path in self.targets)


class _Options(TypedDict, total=False):
    """Zusätzliche Angaben einer Regel (siehe `CoreRule`)."""

    severity: Severity
    allowed: tuple[str, ...]
    attribute: str
    text_equals: str
    chapter: str


def _rule(
    rule_id: str,
    kind: RuleKind,
    context: str,
    target: str | tuple[str, ...],
    source: tuple[str, str],
    **options: Unpack[_Options],
) -> CoreRule:
    """Baut eine Regel; Pfade stehen mit `/` getrennt, Alternativen als Tupel."""
    alternatives = (target,) if isinstance(target, str) else target
    return CoreRule(
        id=rule_id,
        kind=kind,
        context=context,
        targets=tuple(tuple(alternative.split("/")) for alternative in alternatives),
        severity=options.get(
            "severity", Severity.INFO if kind is RuleKind.EXPECTED else Severity.ERROR
        ),
        template=source[0],
        lines=source[1],
        allowed=options.get("allowed", ()),
        attribute=options.get("attribute"),
        text_equals=options.get("text_equals"),
        chapter=options.get("chapter", str(CHAPTER_TIMETABLE)),
    )


_SJ: Final = "ServiceJourney.xml"
_SJP: Final = "ServiceJourneyPattern.xml"
_TDT: Final = "TimeDemandType.xml"
_TL: Final = "TimingLink.xml"
_JP: Final = "JourneyPart.xml"
_POINT: Final = "StopPointInJourneyPattern"
_RUN: Final = "JourneyRunTime"
_WAIT: Final = "JourneyWaitTime"
_REQUIRED: Final = RuleKind.REQUIRED
_ONE: Final = RuleKind.EXACTLY_ONE
_FORBIDDEN: Final = RuleKind.FORBIDDEN
_VALUE: Final = RuleKind.VALUE
_EXPECTED: Final = RuleKind.EXPECTED

CORE_RULES: Final = (
    _rule("CH-SJ-01", _ONE, JOURNEY, "validityConditions/AvailabilityConditionRef", (_SJ, "13-19")),
    _rule("CH-SJ-02", _REQUIRED, JOURNEY, "ServiceAlteration", (_SJ, "87-92")),
    _rule("CH-SJ-03", _VALUE, JOURNEY, "ServiceAlteration", (_SJ, "89-91"), allowed=("planned",)),
    _rule("CH-SJ-04", _ONE, JOURNEY, PATTERN_REF, (_SJ, "99-102")),
    _rule("CH-SJ-05", _ONE, JOURNEY, "TimeDemandTypeRef", (_SJ, "103-106")),
    _rule("CH-SJ-06", _REQUIRED, JOURNEY, "trainNumbers/TrainNumberRef", (_SJ, "117-122")),
    _rule("CH-SJ-07", _REQUIRED, JOURNEY, "TypeOfProductCategoryRef", (_SJ, "59-62")),
    _rule("CH-SJ-08", _EXPECTED, JOURNEY, "DepartureTime", (_SJ, "93")),
    _rule("CH-SJ-09", _FORBIDDEN, JOURNEY, "PrivateCode", (_SJ, "50-54")),
    _rule("CH-SJ-10", _FORBIDDEN, JOURNEY, "LineRef", (_SJ, "112-115")),
    _rule("CH-SJ-11", _FORBIDDEN, JOURNEY, "DirectionType", (_SJ, "116")),
    _rule("CH-SJ-12", _FORBIDDEN, JOURNEY, "passingTimes", (_SJ, "129-134")),
    _rule("CH-SJ-13", _FORBIDDEN, JOURNEY, "calls", (_SJ, "145-153")),
    _rule(
        "CH-SJ-14",
        _FORBIDDEN,
        JOURNEY,
        "keyList/KeyValue/Key",
        (_SJ, "21-23"),
        text_equals="sjyid",
    ),
    _rule(
        "CH-SJ-15",
        _VALUE,
        JOURNEY,
        "TypeOfServiceRef",
        (_SJ, "63-66"),
        severity=Severity.INFO,
        allowed=("ch:1:TypeOfService:1",),
        attribute="ref",
    ),
    _rule("CH-SJP-01", _REQUIRED, "ServiceJourneyPattern", "RouteView/LineRef", (_SJP, "15-19")),
    _rule("CH-SJP-02", _REQUIRED, "ServiceJourneyPattern", "DirectionType", (_SJP, "21")),
    _rule(
        "CH-SJP-03",
        _REQUIRED,
        "ServiceJourneyPattern",
        f"pointsInSequence/{_POINT}",
        (_SJP, "22-25"),
    ),
    _rule("CH-SJP-04", _REQUIRED, _POINT, "ScheduledStopPointRef", (_SJP, "26-28")),
    _rule("CH-SJP-05", _REQUIRED, _POINT, "ForAlighting", (_SJP, "29")),
    _rule("CH-SJP-06", _REQUIRED, _POINT, "ForBoarding", (_SJP, "30")),
    _rule(
        "CH-SJP-07",
        _VALUE,
        "ServiceJourneyPattern",
        "ServiceJourneyPatternType",
        (_SJP, "70"),
        allowed=("passenger",),
    ),
    _rule("CH-TDT-01", _EXPECTED, "TimeDemandType", f"runTimes/{_RUN}", (_TDT, "61-65")),
    _rule("CH-TDT-02", _REQUIRED, _RUN, "TimingLinkRef", (_TDT, "66-69")),
    _rule("CH-TDT-03", _REQUIRED, _RUN, "RunTime", (_TDT, "70")),
    _rule("CH-TDT-04", _REQUIRED, _WAIT, "WaitTime", (_TDT, "83")),
    _rule(
        "CH-TDT-05",
        _EXPECTED,
        _WAIT,
        ("ScheduledStopPointRef", f"{_POINT}Ref", "TimingPointRef"),
        (_TDT, "79-82"),
    ),
    _rule("CH-TL-01", _REQUIRED, "TimingLink", "FromPointRef", (_TL, "56-60")),
    _rule("CH-TL-02", _REQUIRED, "TimingLink", "ToPointRef", (_TL, "61-65")),
    _rule(
        "CH-JP-01",
        _VALUE,
        "JourneyPart",
        "PurposeOfJourneyPartitionRef",
        (_JP, "86-90"),
        severity=Severity.WARNING,
        chapter=str(CHAPTER_JOURNEY_PARTS),
        # Drei Zwecke laut Guide `d0a8e6d` (templates/JourneyPart.xml Z. 88); beide Schreibweisen
        # von TypeOfProductCategoryChange gelten als erlaubt, auch der Tippfehler „Jouryney“, der
        # in uc05_journey_parts.md Z. 113 weiter vorkommt (Entscheid „Kernregeln Phase 4“ (5)).
        allowed=(
            "ch:1:PurposeOfJourneyPartition:FacilityChange",
            "ch:1:PurposeOfJourneyPartition:DirectCarriage",
            "ch:1:PurposeOfJourneyPartition:TypeOfProductCategoryChange",
            "ch:1:PurposeOfJouryneyPartition:TypeOfProductCategoryChange",
        ),
        attribute="ref",
    ),
)

_VIOLATION_KEYS: Final = {
    RuleKind.REQUIRED: MessageKey.CORE_REQUIRED_MISSING,
    RuleKind.EXACTLY_ONE: MessageKey.CORE_EXACTLY_ONE,
    RuleKind.FORBIDDEN: MessageKey.CORE_FORBIDDEN_PRESENT,
    RuleKind.VALUE: MessageKey.CORE_VALUE_NOT_ALLOWED,
    RuleKind.EXPECTED: MessageKey.CORE_EXPECTED_MISSING,
}


@dataclass(frozen=True)
class RuleFinding:
    """Ein Verstoss: Datei und Diagnose (mit Stelle)."""

    file_id: int
    diagnostic: Diagnostic


class _Walker:
    """Navigiert im Index über Kindelemente; merkt sich die Kinder je Element."""

    def __init__(self, index: DatasetIndex) -> None:
        self._index = index
        self._children: dict[int, list[ElementRow]] = {}

    def children(self, element: ElementRow) -> list[ElementRow]:
        if element.id not in self._children:
            self.prefetch([element])
        return self._children[element.id]

    def prefetch(self, elements: Iterable[ElementRow]) -> None:
        """Lädt die Kinder aller noch unbekannten Elemente gesammelt."""
        missing = [element.id for element in elements if element.id not in self._children]
        self._children.update(self._index.children_of(missing))

    def warm(self, contexts: list[ElementRow], paths: Iterable[Path]) -> None:
        """Lädt vorab alle Kinder, die `find` für diese Kontexte und Pfade braucht."""
        for path in paths:
            current = contexts
            for name in path:
                self.prefetch(current)
                current = [c for parent in current for c in self.children(parent) if c.name == name]

    def find(self, element: ElementRow, path: Path) -> list[ElementRow]:
        """Alle Elemente, die man über die Kindelemente dieses Pfads erreicht."""
        current = [element]
        for name in path:
            current = [
                child for parent in current for child in self.children(parent) if child.name == name
            ]
        return current


def _is_stub_journey(walker: _Walker, journey: ElementRow) -> bool:
    """Rumpf-Fahrt: keine `ServiceJourneyPatternRef`, nur `privateCodes` als Inhalt."""
    names = {child.name for child in walker.children(journey)}
    return PRIVATE_CODES in names and names == {PRIVATE_CODES}


def _finding(
    rule: CoreRule,
    context: ElementRow,
    at: ElementRow,
    key: MessageKey,
    extra: Mapping[str, ParamValue] | None = None,
) -> RuleFinding:
    params: dict[str, ParamValue] = {
        "rule": rule.id,
        "element": context.name,
        "id": context.xml_id or "",
        "path": rule.path_text,
        "source": rule.source,
        "chapter": rule.chapter,
        **(extra or {}),
    }
    diagnostic = Diagnostic(
        DiagnosticCategory.PROFILE_RULE, rule.severity, key, params, position=at.start
    )
    return RuleFinding(context.file_id, diagnostic)


def _check_rule(rule: CoreRule, context: ElementRow, walker: _Walker) -> Iterable[RuleFinding]:
    matches = [match for path in rule.targets for match in walker.find(context, path)]
    key = _VIOLATION_KEYS[rule.kind]
    if rule.kind in {RuleKind.REQUIRED, RuleKind.EXPECTED}:
        if not matches:
            yield _finding(rule, context, context, key)
    elif rule.kind is RuleKind.EXACTLY_ONE:
        if len(matches) != 1:
            yield _finding(
                rule, context, matches[1] if matches else context, key, {"found": len(matches)}
            )
    elif rule.kind is RuleKind.FORBIDDEN:
        for match in matches:
            if rule.text_equals is None or match.text.strip() == rule.text_equals:
                yield _finding(rule, context, match, key)
    else:
        for match in matches:
            value = match.attributes.get(rule.attribute) if rule.attribute else match.text.strip()
            if value is not None and value not in rule.allowed:
                shown = {"value": value[:200], "allowed": ", ".join(rule.allowed)}
                yield _finding(rule, context, match, key, shown)


def check_core_rules(
    index: DatasetIndex, file_ids: frozenset[int], rules: Iterable[CoreRule] = CORE_RULES
) -> list[RuleFinding]:
    """Prüft die Kernregeln in den Dateien `file_ids`; Verstösse nach Datei und Stelle sortiert."""
    rule_list = list(rules)
    walker = _Walker(index)
    contexts: dict[str, list[ElementRow]] = {}
    for element in index.elements_named(sorted({rule.context for rule in rule_list})):
        if element.file_id in file_ids:
            contexts.setdefault(element.name, []).append(element)
    findings: list[RuleFinding] = []
    walker.prefetch(contexts.get(JOURNEY, ()))
    stubs = {
        journey.id for journey in contexts.get(JOURNEY, ()) if _is_stub_journey(walker, journey)
    }
    for journey in contexts.get(JOURNEY, ()):
        if journey.id in stubs:
            diagnostic = Diagnostic(
                DiagnosticCategory.PROFILE_RULE,
                Severity.INFO,
                MessageKey.CORE_STUB_JOURNEY,
                {"element": journey.name, "id": journey.xml_id or ""},
                position=journey.start,
            )
            findings.append(RuleFinding(journey.file_id, diagnostic))
    for rule in rule_list:
        checked = [c for c in contexts.get(rule.context, ()) if c.id not in stubs]
        walker.warm(checked, rule.targets)
        for context in checked:
            findings.extend(_check_rule(rule, context, walker))
    findings.sort(
        key=lambda f: (f.file_id, f.diagnostic.position.byte if f.diagnostic.position else 0)
    )
    return findings
