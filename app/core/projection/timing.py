"""Zeiten an den Halten einer Fahrt berechnen, mit Rechenkette und Herkunft jedes Summanden.

Belege in docs/mapping.md: Z2 bis Z7, M1 bis M3.

- Abfahrt am ersten Halt: `ServiceJourney/DepartureTime` (Z2), verschoben um
  `DepartureDayOffset`; fehlt dieses, gilt 0 als **Standardwert** (M2, gekennzeichnet).
- Ankunft am nächsten Halt: vorherige Abfahrt + `JourneyRunTime/RunTime` des `TimingLink` (Z3).
  Den `TimingLink` nennt `OnwardTimingLinkRef` des vorherigen Halts; fehlt er, gilt der
  `TimingLink`, dessen `FromPointRef`/`ToPointRef` zu den beiden Halten passen (Z4, mit Hinweis).
- Abfahrt am Halt: Ankunft + `JourneyWaitTime/WaitTime` (Z5). Ohne `JourneyWaitTime` gilt 0
  (der Guide verlangt Wartezeiten nur, wenn sie grösser als 0 sind); als Standardwert
  gekennzeichnet.
- Fehlt ein Summand oder ist er nicht eindeutig, ist die Zeit „nicht berechenbar“ mit Grund; alle
  folgenden Zeiten ebenfalls (Z7). Nichts wird ersetzt.
- Der Tageswechsel folgt allein aus dem Aufsummieren (M3).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Final

from app.core.index.dataset_index import DatasetIndex, ElementRow
from app.core.messages import MessageKey, ParamValue, Severity
from app.core.projection.clock import (
    SECONDS_PER_DAY,
    parse_day_offset,
    parse_duration,
    parse_time_of_day,
)
from app.core.projection.common import (
    Finding,
    Lookup,
    LookupStatus,
    child,
    children,
    follow,
    follow_child,
    text_of,
)

_WAIT_REF_NAMES: Final = ("StopPointInJourneyPatternRef", "ScheduledStopPointRef", "TimingPointRef")


class TimeStatus(StrEnum):
    """Herkunft einer Zeit."""

    EXPLICIT = "explicit"
    """Steht so in der Datei (`DepartureTime`)."""
    COMPUTED = "computed"
    NOT_COMPUTABLE = "not_computable"


class OffsetOrigin(StrEnum):
    """Woher die Tagesverschiebung einer Zeit kommt."""

    EXPLICIT = "explicit"
    """`DepartureDayOffset` steht in der Datei."""
    DEFAULT = "default"
    """`DepartureDayOffset` fehlt; 0 ist ein Standardwert."""
    COMPUTED = "computed"
    """Durch das Aufsummieren hat die Zeit einen anderen Tag erreicht als die Abfahrt."""


class StepKind(StrEnum):
    """Art eines Summanden der Rechenkette."""

    DEPARTURE_TIME = "departure_time"
    DAY_OFFSET = "day_offset"
    RUN_TIME = "run_time"
    WAIT_TIME = "wait_time"


@dataclass(frozen=True)
class CalcStep:
    """Ein Summand der Rechenkette mit Quelle und Zwischenstand."""

    kind: StepKind
    value: str | None
    """Text aus der Datei; `None` bei einem Standardwert."""
    element: ElementRow | None
    """Quelle des Werts; `None` bei einem Standardwert."""
    default: bool
    seconds: int
    total: int
    """Zwischenstand nach diesem Summanden, in Sekunden seit Mitternacht des Betriebstags."""
    related: tuple[ElementRow, ...] = ()
    """Weitere beteiligte Objekte (`TimingLink`, `JourneyRunTime`, `JourneyWaitTime`)."""
    via_from_to: bool = False
    """Der `TimingLink` wurde über Von-/Nach-Punkt bestimmt (kein `OnwardTimingLinkRef`)."""


@dataclass(frozen=True)
class TimeResult:
    """Eine Zeit an einem Halt (Ankunft oder Abfahrt)."""

    id: str
    status: TimeStatus
    total: int | None
    """Sekunden seit Mitternacht des Betriebstags (auch über 24 Stunden); `None` = unberechenbar."""
    source: ElementRow | None
    chain: tuple[CalcStep, ...]
    reason: Finding | None
    offset_origin: OffsetOrigin | None


@dataclass(frozen=True)
class StopTimes:
    """Ankunft und Abfahrt eines Halts (erster Halt ohne Ankunft, letzter ohne Abfahrt)."""

    arrival: TimeResult | None
    departure: TimeResult | None


@dataclass(frozen=True)
class TimingResult:
    """Zeiten aller Halte und Befunde (Ursachen, Standardwerte, Hinweise)."""

    stops: list[StopTimes]
    findings: list[Finding]


@dataclass(frozen=True)
class _Run:
    journey_run_time: ElementRow
    link: ElementRow | None
    duration: ElementRow | None


@dataclass(frozen=True)
class _Wait:
    journey_wait_time: ElementRow
    ref_name: str
    target: ElementRow | None
    ref: str
    duration: ElementRow | None


@dataclass(frozen=True)
class _Link:
    element: ElementRow
    from_target: ElementRow | None
    from_ref: str
    to_target: ElementRow | None
    to_ref: str


@dataclass
class _Context:
    index: DatasetIndex
    stops: list[ElementRow]
    runs: list[_Run] = field(default_factory=list)
    waits: list[_Wait] = field(default_factory=list)
    links: list[_Link] | None = None
    from_to_links: list[ElementRow] = field(default_factory=list)


def _ref_target(index: DatasetIndex, ref: ElementRow | None) -> tuple[ElementRow | None, str]:
    if ref is None:
        return None, ""
    return index.resolve(ref).target, ref.attributes.get("ref", "")


def _matches(target: ElementRow | None, ref: str, candidate: ElementRow | None) -> bool:
    if candidate is None:
        return False
    if target is not None:
        return target.id == candidate.id
    return candidate.xml_id is not None and ref == candidate.xml_id


def _read_runs(index: DatasetIndex, demand: ElementRow) -> list[_Run]:
    runs = []
    for container in children(index, demand, "runTimes"):
        for item in children(index, container, "JourneyRunTime"):
            link, _ = _ref_target(index, child(index, item, "TimingLinkRef"))
            runs.append(_Run(item, link, child(index, item, "RunTime")))
    return runs


def _read_waits(index: DatasetIndex, demand: ElementRow) -> list[_Wait]:
    waits = []
    for container in children(index, demand, "waitTimes"):
        for item in children(index, container, "JourneyWaitTime"):
            duration = child(index, item, "WaitTime")
            for name in _WAIT_REF_NAMES:
                ref = child(index, item, name)
                if ref is not None:
                    target, text = _ref_target(index, ref)
                    waits.append(_Wait(item, name, target, text, duration))
    return waits


def _read_links(context: _Context) -> list[_Link]:
    if context.links is None:
        index = context.index
        context.links = []
        for link in index.elements_by_name(("TimingLink",)):
            from_target, from_ref = _ref_target(index, child(index, link, "FromPointRef"))
            to_target, to_ref = _ref_target(index, child(index, link, "ToPointRef"))
            context.links.append(_Link(link, from_target, from_ref, to_target, to_ref))
    return context.links


def _scheduled_stop_point(index: DatasetIndex, stop: ElementRow) -> ElementRow | None:
    target, _ = follow_child(index, stop, "ScheduledStopPointRef")
    return target


def _has_run(context: _Context, link: ElementRow) -> bool:
    return any(run.link is not None and run.link.id == link.id for run in context.runs)


@dataclass(frozen=True)
class _Start:
    steps: tuple[CalcStep, ...]
    departure_element: ElementRow
    offset_element: ElementRow | None
    base_day: int


def _link_from_to(context: _Context, position: int) -> ElementRow | Finding:
    """`TimingLink` zwischen zwei Halten über Von-/Nach-Punkt (Z4, zweiter Weg)."""
    previous, current = context.stops[position - 1], context.stops[position]
    from_point = _scheduled_stop_point(context.index, previous)
    to_point = _scheduled_stop_point(context.index, current)
    if from_point is None or to_point is None:
        # Nummer (ab 1) des Halts, dessen Fahrplanpunkt sich nicht auflösen lässt.
        number = position + 1 if to_point is None else position
        missing = current if to_point is None else previous
        return Finding(
            Severity.WARNING, MessageKey.TIME_STOP_UNAVAILABLE, {"position": number}, missing
        )
    candidates = [
        link.element
        for link in _read_links(context)
        if _matches(link.from_target, link.from_ref, from_point)
        and _matches(link.to_target, link.to_ref, to_point)
    ]
    if len(candidates) > 1:
        # Mehrere TimingLinks zwischen denselben Punkten: nur die mit RunTime in diesem
        # TimeDemandType kommen in Frage.
        candidates = [link for link in candidates if _has_run(context, link)]
    if len(candidates) == 1:
        context.from_to_links.append(candidates[0])
        return candidates[0]
    key = (
        MessageKey.TIME_TIMING_LINK_AMBIGUOUS
        if candidates
        else MessageKey.TIME_TIMING_LINK_NOT_FOUND
    )
    params = {"from": from_point.xml_id or "", "to": to_point.xml_id or ""}
    return Finding(Severity.WARNING, key, params, previous)


def _timing_link(context: _Context, position: int) -> tuple[ElementRow | Finding, bool]:
    """`TimingLink` der Strecke zum Halt `position` (Z4) und ob er über Von-/Nach-Punkt kam."""
    onward = child(context.index, context.stops[position - 1], "OnwardTimingLinkRef")
    if onward is None:
        found = _link_from_to(context, position)
        return found, not isinstance(found, Finding)
    link, _ = follow(context.index, onward)
    if link is None:
        failure = Finding(
            Severity.WARNING,
            MessageKey.TIME_TIMING_LINK_UNRESOLVED,
            {"ref": onward.attributes.get("ref", "")},
            onward,
        )
        return failure, False
    return link, False


def _duration_step(
    kind: StepKind,
    element: ElementRow | None,
    previous_total: int,
    related: tuple[ElementRow, ...],
    via_from_to: bool = False,
) -> CalcStep | Finding | None:
    """Summand aus einer Dauer; `None`, wenn das Element fehlt oder leer ist."""
    value = text_of(element)
    if element is None or value.text is None:
        return None
    seconds = parse_duration(value.text)
    if seconds is None:
        return Finding(
            Severity.WARNING, MessageKey.TIME_DURATION_INVALID, {"value": value.text}, element
        )
    return CalcStep(
        kind, value.text, element, False, seconds, previous_total + seconds, related, via_from_to
    )


def _run_step(context: _Context, position: int, previous_total: int) -> CalcStep | Finding:
    link, via_from_to = _timing_link(context, position)
    if isinstance(link, Finding):
        return link
    matches = [run for run in context.runs if run.link is not None and run.link.id == link.id]
    params = {"link": link.xml_id or ""}
    if len(matches) > 1:
        return Finding(Severity.WARNING, MessageKey.TIME_RUN_TIME_AMBIGUOUS, params, link)
    result = (
        _duration_step(
            StepKind.RUN_TIME,
            matches[0].duration,
            previous_total,
            (link, matches[0].journey_run_time),
            via_from_to,
        )
        if matches
        else None
    )
    if result is None:
        return Finding(Severity.WARNING, MessageKey.TIME_RUN_TIME_MISSING, params, link)
    return result


def _wait_step(context: _Context, position: int, arrival_total: int) -> CalcStep | Finding:
    stop = context.stops[position]
    point = _scheduled_stop_point(context.index, stop)
    own = [
        wait
        for wait in context.waits
        if wait.ref_name == "StopPointInJourneyPatternRef" and _matches(wait.target, wait.ref, stop)
    ]
    # Der Verweis auf das StopPointInJourneyPattern übersteuert den auf den ScheduledStopPoint.
    matches = own or [
        wait
        for wait in context.waits
        if wait.ref_name != "StopPointInJourneyPatternRef"
        and _matches(wait.target, wait.ref, point)
    ]
    if len(matches) > 1:
        return Finding(
            Severity.WARNING, MessageKey.TIME_WAIT_TIME_AMBIGUOUS, {"position": position + 1}, stop
        )
    result = (
        _duration_step(
            StepKind.WAIT_TIME,
            matches[0].duration,
            arrival_total,
            (matches[0].journey_wait_time,),
        )
        if matches
        else None
    )
    # Ohne JourneyWaitTime gilt 0 als Standardwert (Z5).
    return result or CalcStep(StepKind.WAIT_TIME, None, None, True, 0, arrival_total)


def _start(index: DatasetIndex, journey: ElementRow) -> _Start | Finding:
    """Abfahrt am ersten Halt mit Tagesverschiebung (Z2, M1, M2) oder der Grund, warum sie fehlt."""
    element = child(index, journey, "DepartureTime")
    value = text_of(element)
    if element is None or value.text is None:
        return Finding(Severity.WARNING, MessageKey.TIME_DEPARTURE_MISSING, {}, journey)
    clock = parse_time_of_day(value.text)
    if clock is None:
        return Finding(
            Severity.WARNING, MessageKey.TIME_DEPARTURE_INVALID, {"value": value.text}, element
        )
    offset_element = child(index, journey, "DepartureDayOffset")
    offset_text = text_of(offset_element)
    days = 0
    if offset_text.text is not None:
        parsed = parse_day_offset(offset_text.text)
        if parsed is None:
            return Finding(
                Severity.WARNING,
                MessageKey.TIME_DAY_OFFSET_INVALID,
                {"value": offset_text.text},
                offset_element,
            )
        days = parsed
    explicit = offset_text.text is not None
    offset_step = CalcStep(
        StepKind.DAY_OFFSET,
        offset_text.text,
        offset_element if explicit else None,
        not explicit,
        days * SECONDS_PER_DAY,
        clock + days * SECONDS_PER_DAY,
    )
    departure_step = CalcStep(StepKind.DEPARTURE_TIME, value.text, element, False, clock, clock)
    return _Start(
        (departure_step, offset_step), element, offset_element if explicit else None, days
    )


def _origin(start: _Start, total: int) -> OffsetOrigin:
    if total // SECONDS_PER_DAY != start.base_day:
        return OffsetOrigin.COMPUTED
    return OffsetOrigin.EXPLICIT if start.offset_element is not None else OffsetOrigin.DEFAULT


def _failed(identifier: str, reason: Finding) -> TimeResult:
    return TimeResult(identifier, TimeStatus.NOT_COMPUTABLE, None, None, (), reason, None)


def _first_departure(start: _Start) -> TimeResult:
    """Abfahrt am ersten Halt: steht in der Datei (`DepartureTime` + Tagesverschiebung)."""
    total = start.steps[-1].total
    return TimeResult(
        "departure-1",
        TimeStatus.EXPLICIT,
        total,
        start.departure_element,
        start.steps,
        None,
        _origin(start, total),
    )


def _computed(
    identifier: str, start: _Start, chain: tuple[CalcStep, ...], source: ElementRow | None
) -> TimeResult:
    total = chain[-1].total
    return TimeResult(
        identifier, TimeStatus.COMPUTED, total, source, chain, None, _origin(start, total)
    )


def _walk(
    context: _Context, start: _Start, findings: list[Finding]
) -> tuple[list[TimeResult | None], list[TimeResult | None]]:
    """Summiert Strecke für Strecke; bei der ersten Lücke bricht die Kette ab."""
    count = len(context.stops)
    arrivals: list[TimeResult | None] = [None] * count
    departures: list[TimeResult | None] = [None] * count
    departures[0] = _first_departure(start)
    chain = start.steps
    for position in range(1, count):
        run = _run_step(context, position, chain[-1].total)
        if isinstance(run, Finding):
            findings.append(run)
            break
        chain = (*chain, run)
        arrivals[position] = _computed(f"arrival-{position + 1}", start, chain, run.element)
        if position == count - 1:
            break
        wait = _wait_step(context, position, chain[-1].total)
        if isinstance(wait, Finding):
            findings.append(wait)
            break
        chain = (*chain, wait)
        departures[position] = _computed(f"departure-{position + 1}", start, chain, wait.element)
    return arrivals, departures


def _assemble(
    count: int,
    arrivals: list[TimeResult | None],
    departures: list[TimeResult | None],
    reason: Finding | None,
) -> list[StopTimes]:
    """Fügt die Zeiten zusammen; fehlende werden mit dem Grund der Lücke „nicht berechenbar“."""
    stops = []
    for position in range(count):
        arrival = arrivals[position]
        departure = departures[position]
        if reason is not None:
            if arrival is None and position > 0:
                arrival = _failed(f"arrival-{position + 1}", reason)
            if departure is None and position < count - 1:
                departure = _failed(f"departure-{position + 1}", reason)
        stops.append(StopTimes(arrival, departure))
    return stops


def compute_times(
    index: DatasetIndex, journey: ElementRow, stops: list[ElementRow]
) -> TimingResult:
    """Berechnet Ankunft und Abfahrt aller Halte (`stops` in XML-Reihenfolge)."""
    if not stops:
        return TimingResult([], [])
    count = len(stops)
    start = _start(index, journey)
    if isinstance(start, Finding):
        return TimingResult(_assemble(count, [None] * count, [None] * count, start), [start])
    findings: list[Finding] = []
    if start.offset_element is None:
        findings.append(Finding(Severity.INFO, MessageKey.DAY_OFFSET_DEFAULT, {}, journey))
    demand, problem = follow_child(index, journey, "TimeDemandTypeRef")
    context = _Context(index, stops)
    reason: Finding | None = None
    if demand is None:
        reason = _demand_failure(journey, problem)
        findings.append(reason)
        arrivals: list[TimeResult | None] = [None] * count
        departures: list[TimeResult | None] = [None] * count
        departures[0] = _first_departure(start)
    else:
        context.runs = _read_runs(index, demand)
        context.waits = _read_waits(index, demand)
        before = len(findings)
        arrivals, departures = _walk(context, start, findings)
        reason = findings[before] if len(findings) > before else None
    if context.from_to_links:
        link = context.from_to_links[0]
        params: dict[str, ParamValue] = {
            "legs": len(context.from_to_links),
            "link": link.xml_id or "",
        }
        findings.append(Finding(Severity.INFO, MessageKey.TIMING_LINK_FROM_TO, params, link))
    return TimingResult(_assemble(count, arrivals, departures, reason), findings)


def _demand_failure(journey: ElementRow, problem: Lookup | None) -> Finding:
    if problem is not None and problem.status is not LookupStatus.ABSENT:
        return Finding(
            Severity.WARNING,
            MessageKey.TIME_DEMAND_UNRESOLVED,
            {"ref": problem.text or ""},
            problem.element,
        )
    return Finding(Severity.WARNING, MessageKey.TIME_DEMAND_MISSING, {}, journey)
