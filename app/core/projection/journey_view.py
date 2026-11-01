"""Fahrtansicht CH 2.0: eine `ServiceJourney` als Fahrplan, jede Angabe mit Herkunft.

Belege in docs/mapping.md (Regeln H, E, L, Z, M, B, F, V, A, N, P):

- Haltefolge in **XML-Reihenfolge** der `StopPointInJourneyPattern` (H2); das Attribut `order` ist
  nicht erlaubt und führt bei Abweichung nur zu einem Hinweis (H3).
- Halt → `ScheduledStopPoint` → `PassengerStopAssignment` → `StopPlace`/`Quay` (H4); fehlt die
  Zuordnung, steht der Grund da („Haltestelle nicht in dieser Datei“ ohne `StopPlace` im Datensatz).
- Zeiten berechnet mit Rechenkette ([timing](timing.py)); Tageswechsel („+1“) ausdrücklich oder
  berechnet; Widersprüche zu `JourneyPart`-Zeiten und Nächte der Zeitumstellung als Befunde.
- Betriebstage aus `AvailabilityCondition` ([calendar](calendar.py)), Angebote ([offers](offers.py))
  und Hinweise ([notices](notices.py)).

Nichts wird ergänzt: Was fehlt oder sich nicht auflösen lässt, steht mit Grund da.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import pairwise

from app.core.guide.mapping import MappingTable
from app.core.index.dataset_index import DatasetIndex, ElementRow
from app.core.messages import MessageKey, ParamValue, Severity
from app.core.projection.calendar import Validity, dst_nights, validities
from app.core.projection.clock import (
    SECONDS_PER_DAY,
    parse_day_offset,
    parse_time_of_day,
    split_seconds,
)
from app.core.projection.common import (
    ABSENT,
    Finding,
    LangText,
    Lookup,
    LookupStatus,
    child,
    children,
    follow_child,
    multilingual,
    text_of,
)
from app.core.projection.journeys import (
    JOURNEY_TYPES,
    line_of,
    stop_name,
    train_number,
    train_numbers_of,
)
from app.core.projection.master_data import lookup_master
from app.core.projection.notices import NoticeView, journey_notices, unassigned_count
from app.core.projection.offers import (
    STOP_USE_COLUMN,
    STOP_USE_SHEET,
    CategoryView,
    CodedValue,
    FacilitySetView,
    TransportView,
    category,
    facility_sets,
    transport,
)
from app.core.projection.timing import StopTimes, TimeResult, compute_times


@dataclass(frozen=True)
class PrivateCodeView:
    """Ein `PrivateCode` der Fahrt (z. B. `type="sjyid"`)."""

    code_type: str | None
    value: str
    element: ElementRow


@dataclass(frozen=True)
class StopView:
    """Ein Halt der Fahrt mit Ein-/Aussteigen, Zeiten und Zuordnung."""

    position: int
    point: ElementRow
    stop_point: Lookup
    """Name des `ScheduledStopPoint` (Fahrplanpunkt)."""
    stop_place: Lookup
    """Name der `StopPlace` (Haltestelle) laut `PassengerStopAssignment`."""
    quay: Lookup
    """`PublicCode` (sonst Name) des `Quay` (Kante) laut `PassengerStopAssignment`."""
    assignment: ElementRow | None
    for_boarding: Lookup
    for_alighting: Lookup
    request_stop: Lookup
    stop_use: CodedValue | None
    times: StopTimes
    part_numbers: tuple[int, ...] = ()
    """Nummern (ab 1) der `JourneyPart`, deren Strecke diesen Halt einschliesst."""


@dataclass(frozen=True)
class PartTime:
    """`StartTime`/`EndTime` einer `JourneyPart` mit ausdrücklicher Tagesverschiebung."""

    time: Lookup
    day_offset: Lookup
    """Fehlt das Element, gilt 0 als Standardwert."""
    total: int | None
    """Sekunden seit Mitternacht des Betriebstags; `None`, wenn nicht lesbar."""


@dataclass(frozen=True)
class PartBoundary:
    """Anfang oder Ende einer `JourneyPart`: Halt aus der Datei und Position in dieser Fahrt."""

    stop: Lookup
    position: int | None
    """Position des Halts in dieser Fahrt (ab 1); `None`, wenn er nicht eindeutig zuzuordnen ist."""


@dataclass(frozen=True)
class PartView:
    """Eine `JourneyPart`: Teilstrecke einer Fahrt mit eigenen Zeiten, Angeboten oder Tagen."""

    number: int
    element: ElementRow
    description: list[LangText]
    purpose: Lookup
    train_numbers: list[Lookup]
    parent_journey: Lookup
    start_stop: PartBoundary
    end_stop: PartBoundary
    start: PartTime
    end: PartTime
    facilities: list[FacilitySetView]
    validity: list[Validity]
    category: CategoryView | None


@dataclass(frozen=True)
class JourneyView:
    """Alles, was die Fahrtansicht zeigt."""

    journey: ElementRow
    pattern: Lookup
    """Das `ServiceJourneyPattern` (Herkunft der Haltefolge) oder der Grund, warum es fehlt."""
    time_demand_type: Lookup
    operator: Lookup
    """Betreiber (`OperatorRef` der Fahrt): Name aus der Datei oder der Grund, warum er fehlt."""
    train_numbers: list[Lookup]
    private_codes: list[PrivateCodeView]
    line: Lookup
    transports: list[TransportView]
    categories: list[CategoryView]
    validities: list[Validity]
    stops: list[StopView]
    parts: list[PartView]
    facilities: list[FacilitySetView]
    notices: list[NoticeView]
    findings: list[Finding]


def is_journey(element: ElementRow) -> bool:
    """Ob das Element eine Fahrt ist, für die es eine Fahrtansicht gibt."""
    return element.name in JOURNEY_TYPES


def _stop_points(index: DatasetIndex, pattern: ElementRow | None) -> list[ElementRow]:
    container = None if pattern is None else child(index, pattern, "pointsInSequence")
    return [] if container is None else children(index, container, "StopPointInJourneyPattern")


def _named(target: ElementRow | None, problem: Lookup | None, label: Lookup) -> Lookup:
    if target is None:
        return problem or ABSENT
    return label if label.element else Lookup(LookupStatus.ABSENT, None, target)


def _name_of(index: DatasetIndex, element: ElementRow) -> Lookup:
    """Name aus der Datei (`label` des Objekts, Quelle ist das `Name`-Element)."""
    if element.label:
        return Lookup(LookupStatus.FOUND, element.label, child(index, element, "Name") or element)
    return Lookup(LookupStatus.ABSENT, None, element)


def _assignments(index: DatasetIndex, point: ElementRow) -> list[ElementRow]:
    """Alle `PassengerStopAssignment`, die den Fahrplanpunkt nennen (ohne Obergrenze)."""
    return index.referencing_parents(point, ("ScheduledStopPointRef",), "PassengerStopAssignment")


def _quay(index: DatasetIndex, assignment: ElementRow) -> Lookup:
    target, problem = follow_child(index, assignment, "QuayRef")
    if target is None:
        return problem or Lookup(LookupStatus.ABSENT, None, assignment)
    code = text_of(child(index, target, "PublicCode"))
    return code if code.element else _name_of(index, target)


def _places(
    index: DatasetIndex, point: ElementRow | None, has_stop_places: bool
) -> tuple[Lookup, Lookup, ElementRow | None]:
    """Haltestelle und Kante des Fahrplanpunkts (H4); der Grund steht da, wenn sie fehlen."""
    if point is None:
        return ABSENT, ABSENT, None
    assignments = _assignments(index, point)
    if not assignments:
        status = LookupStatus.ABSENT if has_stop_places else LookupStatus.EXTERNAL_OR_UNLOADED
        missing = Lookup(status, point.xml_id)
        return missing, missing, None
    if len(assignments) > 1:
        many = Lookup(LookupStatus.AMBIGUOUS, point.xml_id, assignments[0])
        return many, many, assignments[0]
    assignment = assignments[0]
    place, problem = follow_child(index, assignment, "StopPlaceRef")
    stop_place = problem if place is None else _name_of(index, place)
    return stop_place or ABSENT, _quay(index, assignment), assignment


def _stop_use(index: DatasetIndex, point: ElementRow, table: MappingTable) -> CodedValue | None:
    element = child(index, point, "StopUse")
    value = text_of(element)
    if element is None or value.text is None:
        return None
    master = lookup_master(table, STOP_USE_SHEET, STOP_USE_COLUMN, value.text)
    return CodedValue(value.text, element, master)


def _order_finding(points: list[ElementRow]) -> Finding | None:
    """Hinweis, wenn das (nicht erlaubte) Attribut `order` der XML-Reihenfolge widerspricht (H3)."""
    orders = [point.attributes.get("order") for point in points]
    if not points or any(order is None or not order.strip().isdigit() for order in orders):
        return None
    numbers = [int(order) for order in orders if order is not None]
    if all(first < second for first, second in pairwise(numbers)):
        return None
    return Finding(Severity.INFO, MessageKey.STOP_ORDER_DIFFERS, {}, points[0])


def _part_numbers(parts: list[PartView], stop_count: int) -> list[tuple[int, ...]]:
    """Je Halt die Nummern der Teilstrecken, die ihn einschliessen."""
    return [
        tuple(part.number for part in parts if position in _covered(part, stop_count))
        for position in range(1, stop_count + 1)
    ]


def _stop_views(
    index: DatasetIndex,
    points: list[ElementRow],
    times: list[StopTimes],
    part_numbers: list[tuple[int, ...]],
    table: MappingTable,
) -> list[StopView]:
    has_stop_places = index.has_object_type("StopPlace")
    views = []
    rows = zip(points, times, part_numbers, strict=True)
    for position, (point, stop_times, numbers) in enumerate(rows, start=1):
        scheduled, _ = follow_child(index, point, "ScheduledStopPointRef")
        place, quay, assignment = _places(index, scheduled, has_stop_places)
        views.append(
            StopView(
                position=position,
                point=point,
                stop_point=stop_name(index, point),
                stop_place=place,
                quay=quay,
                assignment=assignment,
                for_boarding=text_of(child(index, point, "ForBoarding")),
                for_alighting=text_of(child(index, point, "ForAlighting")),
                request_stop=text_of(child(index, point, "RequestStop")),
                stop_use=_stop_use(index, point, table),
                times=stop_times,
                part_numbers=numbers,
            )
        )
    return views


def _part_time(index: DatasetIndex, part: ElementRow, time_name: str, offset_name: str) -> PartTime:
    time = text_of(child(index, part, time_name))
    offset = text_of(child(index, part, offset_name))
    clock = None if time.text is None else parse_time_of_day(time.text)
    days = 0 if offset.text is None else parse_day_offset(offset.text)
    total = None if clock is None or days is None else clock + days * SECONDS_PER_DAY
    return PartTime(time, offset, total)


def _boundary(
    index: DatasetIndex,
    part: ElementRow,
    stops: list[ElementRow],
    names: tuple[str, str],
) -> PartBoundary:
    """Anfang/Ende einer Teilstrecke über `…StopPointRef` oder `…PointInPatternRef`."""
    stop_ref, point_ref = names
    target, problem = follow_child(index, part, stop_ref)
    if target is not None:
        matches = [
            number
            for number, stop in enumerate(stops, start=1)
            if (scheduled := follow_child(index, stop, "ScheduledStopPointRef")[0]) is not None
            and scheduled.id == target.id
        ]
        position = matches[0] if len(matches) == 1 else None
        return PartBoundary(_named(target, None, _name_of(index, target)), position)
    if problem is not None and problem.status is not LookupStatus.ABSENT:
        return PartBoundary(problem, None)
    pointer, pointer_problem = follow_child(index, part, point_ref)
    if pointer is None:
        return PartBoundary(pointer_problem or ABSENT, None)
    position = next((number for number, stop in enumerate(stops, 1) if stop.id == pointer.id), None)
    return PartBoundary(stop_name(index, pointer), position)


def _purpose(index: DatasetIndex, part: ElementRow) -> Lookup:
    target, problem = follow_child(index, part, "PurposeOfJourneyPartitionRef")
    if target is None:
        return problem or ABSENT
    return _named(target, None, text_of(child(index, target, "Name")))


def _parent_journey(index: DatasetIndex, part: ElementRow) -> Lookup:
    target, problem = follow_child(index, part, "ParentJourneyRef")
    if target is None:
        return problem or ABSENT
    return Lookup(LookupStatus.FOUND, target.xml_id, target)


def _part_views(
    index: DatasetIndex, journey: ElementRow, stops: list[ElementRow], table: MappingTable
) -> list[PartView]:
    views = []
    parts = [
        part
        for container in children(index, journey, "parts")
        for part in children(index, container, "JourneyPart")
    ]
    for number, part in enumerate(parts, start=1):
        views.append(
            PartView(
                number=number,
                element=part,
                description=multilingual(index, child(index, part, "Description")),
                purpose=_purpose(index, part),
                train_numbers=[
                    train_number(index, ref) for ref in children(index, part, "TrainNumberRef")
                ],
                parent_journey=_parent_journey(index, part),
                start_stop=_boundary(
                    index, part, stops, ("FromStopPointRef", "FromPointInPatternRef")
                ),
                end_stop=_boundary(index, part, stops, ("ToStopPointRef", "ToPointInPatternRef")),
                start=_part_time(index, part, "StartTime", "StartTimeDayOffset"),
                end=_part_time(index, part, "EndTime", "EndTimeDayOffset"),
                facilities=facility_sets(index, part, table),
                validity=validities(index, part),
                category=category(index, part, "part", table),
            )
        )
    return views


def _covered(part: PartView, stop_count: int) -> range:
    """Positionen (ab 1), die eine Teilstrecke einschliesst; leer, wenn der Anfang unbekannt ist."""
    first = part.start_stop.position
    if first is None:
        return range(0)
    last = part.end_stop.position
    if last is not None:
        return range(first, last + 1)
    if part.end_stop.stop.status is LookupStatus.ABSENT:
        # Fehlt das Ende, reicht die Teilstrecke bis zum Ende der Fahrt (Vorlage JourneyPart.xml).
        return range(first, stop_count + 1)
    # Das Ende ist genannt, lässt sich aber keinem Halt zuordnen: nichts raten.
    return range(0)


def _time_difference(
    part: PartView, field_name: str, stated: PartTime, computed: TimeResult | None
) -> Finding | None:
    if stated.total is None or computed is None or computed.total is None:
        return None
    if stated.total == computed.total:
        return None
    stated_day, stated_clock = split_seconds(stated.total)
    computed_day, computed_clock = split_seconds(computed.total)
    params: dict[str, ParamValue] = {
        "part": part.element.xml_id or "",
        "field": field_name,
        "stated": stated_clock,
        "statedDay": stated_day,
        "computed": computed_clock,
        "computedDay": computed_day,
    }
    return Finding(Severity.WARNING, MessageKey.PART_TIME_DIFFERS, params, stated.time.element)


def _part_findings(parts: list[PartView], stops: list[StopView]) -> list[Finding]:
    """Widersprüche zwischen den Zeiten einer `JourneyPart` und den berechneten Zeiten."""
    findings = []
    for part in parts:
        start, end = part.start_stop.position, part.end_stop.position
        checks = (
            ("StartTime", part.start, None if start is None else stops[start - 1].times.departure),
            ("EndTime", part.end, None if end is None else stops[end - 1].times.arrival),
        )
        for field_name, stated, computed in checks:
            difference = _time_difference(part, field_name, stated, computed)
            if difference is not None:
                findings.append(difference)
    return findings


def _dst_findings(
    validity: list[Validity], stops: list[StopView], journey: ElementRow
) -> list[Finding]:
    totals = [
        time.total
        for stop in stops
        for time in (stop.times.arrival, stop.times.departure)
        if time is not None and time.total is not None
    ]
    days = tuple(
        sorted({day for item in validity if item.days is not None for day in item.days.days})
    )
    if not totals or not days:
        return []
    findings = []
    for night in dst_nights(days, min(totals), max(totals)):
        key = MessageKey.DST_NIGHT_FORWARD if night.forward else MessageKey.DST_NIGHT_BACK
        findings.append(Finding(Severity.INFO, key, {"date": night.date.isoformat()}, journey))
    return findings


def _line(index: DatasetIndex, pattern: ElementRow | None) -> tuple[Lookup, ElementRow | None]:
    """Linie des Fahrtmusters (L1) und das `Line`-Objekt selbst."""
    if pattern is None:
        return ABSENT, None
    route_view = child(index, pattern, "RouteView")
    line, _ = follow_child(index, route_view, "LineRef")
    return line_of(index, pattern), line


def _private_codes(index: DatasetIndex, journey: ElementRow) -> list[PrivateCodeView]:
    return [
        PrivateCodeView(code.attributes.get("type"), code.text.strip(), code)
        for container in children(index, journey, "privateCodes")
        for code in children(index, container, "PrivateCode")
        if code.text.strip()
    ]


def _lookup_of(target: ElementRow | None, problem: Lookup | None) -> Lookup:
    if target is None:
        return problem or ABSENT
    return Lookup(LookupStatus.FOUND, target.xml_id, target)


def build_journey_view(
    index: DatasetIndex, journey: ElementRow, table: MappingTable
) -> JourneyView:
    """Stellt die Fahrtansicht einer `ServiceJourney` zusammen."""
    pattern, pattern_problem = follow_child(index, journey, "ServiceJourneyPatternRef")
    points = _stop_points(index, pattern)
    timing = compute_times(index, journey, points)
    parts = _part_views(index, journey, points, table)
    stops = _stop_views(index, points, timing.stops, _part_numbers(parts, len(points)), table)
    line, line_object = _line(index, pattern)
    demand, demand_problem = follow_child(index, journey, "TimeDemandTypeRef")
    operator, operator_problem = follow_child(index, journey, "OperatorRef")
    own_validities = validities(index, journey)
    findings = list(timing.findings)
    order = _order_finding(points)
    if order is not None:
        findings.append(order)
    for validity in own_validities:
        if validity.days is not None:
            findings.extend(validity.days.findings)
    findings.extend(_part_findings(parts, stops))
    findings.extend(_dst_findings(own_validities, stops, journey))
    unassigned = index.cached("notice_unassigned", lambda: unassigned_count(index))
    if unassigned:
        findings.append(Finding(Severity.INFO, MessageKey.NOTICE_UNASSIGNED, {"count": unassigned}))
    categories = [item for item in (category(index, journey, "journey", table),) if item]
    transports = [transport(index, journey, "journey")]
    if line_object is not None:
        transports.append(transport(index, line_object, "line"))
        line_category = category(index, line_object, "line", table)
        if line_category is not None:
            categories.append(line_category)
    return JourneyView(
        journey=journey,
        pattern=_lookup_of(pattern, pattern_problem),
        time_demand_type=_lookup_of(demand, demand_problem),
        operator=(
            _named(operator, operator_problem, _name_of(index, operator))
            if operator is not None
            else operator_problem or ABSENT
        ),
        train_numbers=train_numbers_of(index, journey),
        private_codes=_private_codes(index, journey),
        line=line,
        transports=transports,
        categories=categories,
        validities=own_validities,
        stops=stops,
        parts=parts,
        facilities=facility_sets(index, journey, table),
        notices=journey_notices(index, journey, pattern, points),
        findings=findings,
    )
