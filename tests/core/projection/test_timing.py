from __future__ import annotations

import pytest

from app.core.messages import MessageKey, Severity
from app.core.projection.clock import split_seconds
from app.core.projection.journey_view import JourneyView
from app.core.projection.timing import OffsetOrigin, StepKind, TimeResult, TimeStatus
from tests.core.projection.builders import (
    Scenario,
    fixture_view,
    link,
    run,
    view_from_xml,
    wait,
)

NOTE = MessageKey.TIMING_LINK_FROM_TO


def clock(time: TimeResult | None) -> str:
    assert time is not None
    assert time.total is not None
    day, text = split_seconds(time.total)
    return f"{text} {day:+d}"


def keys(view: JourneyView) -> list[MessageKey]:
    return [finding.key for finding in view.findings]


def reason_of(time: TimeResult | None) -> MessageKey:
    assert time is not None
    assert time.status is TimeStatus.NOT_COMPUTABLE
    assert time.total is None
    assert time.reason is not None
    return time.reason.key


def test_three_stops_chain_has_a_source_for_every_summand() -> None:
    view = fixture_view("ch20_three_stops.xml")
    first, second, third = (stop.times for stop in view.stops)
    assert first.arrival is None
    assert third.departure is None
    assert [clock(t) for t in (first.departure, second.arrival, second.departure)] == [
        "08:00:00 +0",
        "08:10:00 +0",
        "08:12:00 +0",
    ]
    assert clock(third.arrival) == "08:27:00 +0"
    assert first.departure is not None
    assert first.departure.status is TimeStatus.EXPLICIT
    assert third.arrival is not None
    assert third.arrival.status is TimeStatus.COMPUTED
    chain = third.arrival.chain
    assert [step.kind for step in chain] == [
        StepKind.DEPARTURE_TIME,
        StepKind.DAY_OFFSET,
        StepKind.RUN_TIME,
        StepKind.WAIT_TIME,
        StepKind.RUN_TIME,
    ]
    assert [step.value for step in chain] == ["08:00:00", "0", "PT10M", "PT2M", "PT15M"]
    assert [step.element.name for step in chain if step.element] == [
        "DepartureTime",
        "DepartureDayOffset",
        "RunTime",
        "WaitTime",
        "RunTime",
    ]
    assert not any(step.default for step in chain)
    assert chain[-1].related[0].xml_id == "ch:1:TimingLink:SYN2-3"
    assert [step.via_from_to for step in chain] == [False, False, True, False, True]
    assert chain[-1].total == 8 * 3600 + 27 * 60
    assert keys(view) == [NOTE]


def test_origin_of_day_offset() -> None:
    explicit = fixture_view("ch20_three_stops.xml").stops[0].times.departure
    assert explicit is not None
    assert explicit.offset_origin is OffsetOrigin.EXPLICIT
    default = fixture_view("ch20_midnight.xml", "ch:1:sjyid:SYN:1")
    assert default.stops[0].times.departure is not None
    assert default.stops[0].times.departure.offset_origin is OffsetOrigin.DEFAULT
    assert MessageKey.DAY_OFFSET_DEFAULT in keys(default)


def test_midnight_crossing_is_computed() -> None:
    view = fixture_view("ch20_midnight.xml", "ch:1:sjyid:SYN:1")
    times = [stop.times for stop in view.stops]
    assert clock(times[0].departure) == "23:50:00 +0"
    assert clock(times[1].arrival) == "00:00:00 +1"
    assert clock(times[1].departure) == "00:02:00 +1"
    assert clock(times[2].arrival) == "00:17:00 +1"
    assert times[1].arrival is not None
    assert times[1].arrival.offset_origin is OffsetOrigin.COMPUTED
    assert times[0].departure is not None
    assert times[0].departure.offset_origin is OffsetOrigin.DEFAULT


def test_explicit_day_offset_is_kept() -> None:
    view = fixture_view("ch20_midnight.xml", "ch:1:sjyid:SYN:2")
    first = view.stops[0].times.departure
    assert first is not None
    assert clock(first) == "00:11:00 +1"
    assert first.offset_origin is OffsetOrigin.EXPLICIT
    last = view.stops[2].times.arrival
    assert clock(last) == "00:38:00 +1"
    assert last is not None
    assert last.offset_origin is OffsetOrigin.EXPLICIT
    assert MessageKey.DAY_OFFSET_DEFAULT not in keys(view)


def test_missing_run_time_stops_the_chain() -> None:
    view = fixture_view("ch20_missing_runtime.xml")
    third = view.stops[2].times
    assert reason_of(third.arrival) is MessageKey.TIME_RUN_TIME_MISSING
    assert third.arrival is not None
    assert third.arrival.reason is not None
    assert third.arrival.reason.params == {"link": "ch:1:TimingLink:SYN2-3"}
    assert third.arrival.reason.element is not None
    assert third.arrival.reason.element.xml_id == "ch:1:TimingLink:SYN2-3"
    assert clock(view.stops[1].times.departure) == "08:12:00 +0"
    assert third.departure is None
    warnings = [f for f in view.findings if f.severity is Severity.WARNING]
    assert [f.key for f in warnings] == [MessageKey.TIME_RUN_TIME_MISSING]


def test_onward_timing_link_has_priority_and_no_note() -> None:
    extra = {1: "<OnwardTimingLinkRef ref='tl-ab'/>", 2: "<OnwardTimingLinkRef ref='tl-bc'/>"}
    view = Scenario(points_extra=extra).view()
    assert clock(view.stops[2].times.arrival) == "08:27:00 +0"
    assert NOTE not in keys(view)
    arrival = view.stops[2].times.arrival
    assert arrival is not None
    assert not any(step.via_from_to for step in arrival.chain)


def test_only_one_leg_uses_onward_link() -> None:
    view = Scenario(points_extra={1: "<OnwardTimingLinkRef ref='tl-ab'/>"}).view()
    note = next(f for f in view.findings if f.key is NOTE)
    assert note.params["legs"] == 1


def test_onward_link_unresolved() -> None:
    view = Scenario(points_extra={1: "<OnwardTimingLinkRef ref='fehlt'/>"}).view()
    arrival = view.stops[1].times.arrival
    later = view.stops[2].times.arrival
    assert reason_of(arrival) is MessageKey.TIME_TIMING_LINK_UNRESOLVED
    assert reason_of(later) is MessageKey.TIME_TIMING_LINK_UNRESOLVED
    assert arrival is not None
    assert later is not None
    assert arrival.reason == later.reason


def test_timing_link_not_found() -> None:
    arrival = Scenario(links="").view().stops[1].times.arrival
    assert reason_of(arrival) is MessageKey.TIME_TIMING_LINK_NOT_FOUND
    assert arrival is not None
    assert arrival.reason is not None
    assert arrival.reason.params == {"from": "a", "to": "b"}


def test_several_timing_links_between_the_same_points() -> None:
    links = link("tl-ab", "a", "b") + link("tl-ab2", "a", "b") + link("tl-bc", "b", "c")
    # Nur tl-ab hat eine RunTime in diesem TimeDemandType: die Daten bestimmen die Wahl.
    assert clock(Scenario(links=links).view().stops[1].times.arrival) == "08:10:00 +0"
    both = run("r1", "tl-ab", "PT10M") + run("r3", "tl-ab2", "PT11M")
    arrival = Scenario(links=links, runs=both).view().stops[1].times.arrival
    assert reason_of(arrival) is MessageKey.TIME_TIMING_LINK_AMBIGUOUS


def test_several_timing_links_without_any_run_time_are_ambiguous() -> None:
    links = link("tl-ab", "a", "b") + link("tl-ab2", "a", "b") + link("tl-bc", "b", "c")
    arrival = Scenario(links=links, runs=run("r2", "tl-bc", "PT15M")).view().stops[1].times.arrival
    assert reason_of(arrival) is MessageKey.TIME_TIMING_LINK_AMBIGUOUS


def test_timing_link_is_found_among_many_timing_links() -> None:
    many = "".join(link(f"tl-x{number}", "a", "c") for number in range(600))
    view = Scenario(links=many + link("tl-ab", "a", "b") + link("tl-bc", "b", "c")).view()
    assert clock(view.stops[2].times.arrival) == "08:27:00 +0"


def test_timing_link_matches_unresolved_endpoints_by_id() -> None:
    # Die Punkte der TimingLinks sind nicht auflösbar, ihre ids passen trotzdem zu den Halten.
    unknown = " nameOfRefClass='Unbekannt'"
    view = Scenario(links=link("tl-ab", "a", "b", unknown) + link("tl-bc", "b", "c")).view()
    assert clock(view.stops[2].times.arrival) == "08:27:00 +0"


def test_stop_without_scheduled_stop_point_cannot_be_matched() -> None:
    xml = Scenario().xml()
    xml = xml.replace("<ScheduledStopPointRef ref='b'/>", "<ScheduledStopPointRef ref='x'/>", 1)
    arrival = view_from_xml(xml).stops[1].times.arrival
    assert reason_of(arrival) is MessageKey.TIME_STOP_UNAVAILABLE
    assert arrival is not None
    assert arrival.reason is not None
    assert arrival.reason.params == {"position": 2}


def test_run_time_ambiguous() -> None:
    runs = run("r1", "tl-ab", "PT10M") + run("r1b", "tl-ab", "PT12M")
    arrival = Scenario(runs=runs).view().stops[1].times.arrival
    assert reason_of(arrival) is MessageKey.TIME_RUN_TIME_AMBIGUOUS


def test_run_time_element_missing_or_invalid() -> None:
    arrival = Scenario(runs=run("r1", "tl-ab", None)).view().stops[1].times.arrival
    assert reason_of(arrival) is MessageKey.TIME_RUN_TIME_MISSING
    arrival = Scenario(runs=run("r1", "tl-ab", "P3M")).view().stops[1].times.arrival
    assert reason_of(arrival) is MessageKey.TIME_DURATION_INVALID
    assert arrival is not None
    assert arrival.reason is not None
    assert arrival.reason.params == {"value": "P3M"}
    assert arrival.reason.element is not None
    assert arrival.reason.element.name == "RunTime"


def test_missing_wait_time_is_a_marked_default() -> None:
    view = Scenario(waits="").view()
    assert clock(view.stops[1].times.departure) == "08:10:00 +0"
    departure = view.stops[1].times.departure
    assert departure is not None
    last = departure.chain[-1]
    assert (last.kind, last.default, last.element, last.value) == (
        StepKind.WAIT_TIME,
        True,
        None,
        None,
    )
    assert clock(view.stops[2].times.arrival) == "08:25:00 +0"


def test_wait_time_at_stop_point_in_journey_pattern_overrides() -> None:
    waits = wait("w1", "b", "PT2M") + wait("w2", "p2", "PT5M", "StopPointInJourneyPatternRef")
    view = Scenario(waits=waits).view()
    assert clock(view.stops[1].times.departure) == "08:15:00 +0"


def test_two_wait_times_for_the_same_stop_are_ambiguous() -> None:
    waits = wait("w1", "b", "PT2M") + wait("w2", "b", "PT3M", "TimingPointRef")
    view = Scenario(waits=waits).view()
    arrival, departure = view.stops[1].times.arrival, view.stops[1].times.departure
    assert arrival is not None
    assert arrival.status is TimeStatus.COMPUTED
    assert reason_of(departure) is MessageKey.TIME_WAIT_TIME_AMBIGUOUS
    assert departure is not None
    assert departure.reason is not None
    assert departure.reason.params == {"position": 2}
    assert reason_of(view.stops[2].times.arrival) is MessageKey.TIME_WAIT_TIME_AMBIGUOUS


def test_invalid_wait_time() -> None:
    departure = Scenario(waits=wait("w1", "b", "zwei")).view().stops[1].times.departure
    assert reason_of(departure) is MessageKey.TIME_DURATION_INVALID


def test_wait_time_without_value_is_a_gap_not_a_default() -> None:
    view = Scenario(waits=wait("w1", "b", None)).view()
    departure = view.stops[1].times.departure
    assert reason_of(departure) is MessageKey.TIME_WAIT_TIME_MISSING
    assert departure is not None
    assert departure.reason is not None
    assert departure.reason.params == {"position": 2}
    assert departure.reason.element is not None
    assert departure.reason.element.name == "JourneyWaitTime"
    assert reason_of(view.stops[2].times.arrival) is MessageKey.TIME_WAIT_TIME_MISSING
    assert view.stops[1].times.arrival is not None
    assert view.stops[1].times.arrival.status is TimeStatus.COMPUTED


@pytest.mark.parametrize(
    ("departure", "key"),
    [
        ("", MessageKey.TIME_DEPARTURE_MISSING),
        ("<DepartureTime/>", MessageKey.TIME_DEPARTURE_MISSING),
        ("<DepartureTime>08:00</DepartureTime>", MessageKey.TIME_DEPARTURE_INVALID),
        ("<DepartureTime>08:00:00+01:00</DepartureTime>", MessageKey.TIME_DEPARTURE_INVALID),
    ],
)
def test_departure_problems(departure: str, key: MessageKey) -> None:
    view = Scenario(departure=departure).view()
    assert keys(view) == [key]
    for stop in view.stops:
        for time in (stop.times.arrival, stop.times.departure):
            if time is not None:
                assert reason_of(time) is key
    assert view.stops[0].times.arrival is None
    assert view.stops[2].times.departure is None


def test_utc_departure_is_read_and_all_following_times_are_utc() -> None:
    """Sonderfall Zeitumstellung (mapping.md Z9): `Z` ist UTC, ohne Umrechnung."""
    view = fixture_view("ch20_utc_departure.xml")
    first, second, third = (stop.times for stop in view.stops)
    times = [first.departure, second.arrival, second.departure, third.arrival]
    assert [clock(t) for t in times] == [
        "01:33:00 +0",
        "01:43:00 +0",
        "01:45:00 +0",
        "02:00:00 +0",
    ]
    for time in times:
        assert time is not None
        assert time.utc
        assert all(step.utc for step in time.chain)
    assert first.departure is not None
    assert first.departure.status is TimeStatus.EXPLICIT
    notes = [f for f in view.findings if f.key is MessageKey.TIME_UTC]
    assert [(f.severity, f.element.name if f.element else None) for f in notes] == [
        (Severity.INFO, "DepartureTime")
    ]


def test_local_times_are_not_marked_utc() -> None:
    view = fixture_view("ch20_three_stops.xml")
    for stop in view.stops:
        for time in (stop.times.arrival, stop.times.departure):
            if time is not None:
                assert not time.utc
                assert not any(step.utc for step in time.chain)
    assert MessageKey.TIME_UTC not in keys(view)


def test_utc_departure_without_day_offset_keeps_the_default() -> None:
    view = Scenario(departure="<DepartureTime>02:33:00Z</DepartureTime>").view()
    departure = view.stops[0].times.departure
    assert departure is not None
    assert (departure.utc, departure.offset_origin) == (True, OffsetOrigin.DEFAULT)
    assert MessageKey.DAY_OFFSET_DEFAULT in keys(view)


def test_invalid_day_offset() -> None:
    view = Scenario(day_offset="<DepartureDayOffset>morgen</DepartureDayOffset>").view()
    assert keys(view) == [MessageKey.TIME_DAY_OFFSET_INVALID]


def test_negative_day_offset() -> None:
    view = Scenario(day_offset="<DepartureDayOffset>-1</DepartureDayOffset>").view()
    assert clock(view.stops[0].times.departure) == "08:00:00 -1"
    assert clock(view.stops[2].times.arrival) == "08:27:00 -1"


@pytest.mark.parametrize(
    ("scenario", "key"),
    [
        (Scenario(demand_ref=""), MessageKey.TIME_DEMAND_MISSING),
        (
            Scenario(demand_ref="<TimeDemandTypeRef ref='fehlt'/>"),
            MessageKey.TIME_DEMAND_UNRESOLVED,
        ),
    ],
)
def test_time_demand_type_missing_or_unresolved(scenario: Scenario, key: MessageKey) -> None:
    view = scenario.view()
    assert clock(view.stops[0].times.departure) == "08:00:00 +0"
    assert reason_of(view.stops[1].times.arrival) is key
    assert key in keys(view)


def test_single_stop_pattern() -> None:
    xml = Scenario().xml()
    start = xml.index("<StopPointInJourneyPattern id='p2'>")
    stop = xml.index("</pointsInSequence>")
    view = view_from_xml(xml[:start] + xml[stop:])
    assert len(view.stops) == 1
    assert clock(view.stops[0].times.departure) == "08:00:00 +0"


def test_no_pattern_means_no_stops() -> None:
    view = Scenario(pattern_ref="").view()
    assert view.stops == []
    assert view.pattern.status.value == "absent"
