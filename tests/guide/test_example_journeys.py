"""Fahrtansicht an den Guide-Beispielen 01, 08, 15 und 21 (Abnahme Phase 3).

Die Erwartungen stammen aus der Prüfung der Beispiele vom 31.10.2026 (Guide `b7ac158`). Ändert
sich ein Beispiel, lautet die Meldung „Beispiel geändert, Erwartung prüfen“.
"""

from __future__ import annotations

from pathlib import Path

from app.core.config import load_config
from app.core.dataset import SourceFile, open_dataset
from app.core.guide.examples import examples_dir
from app.core.guide.layout import MAPPING_TABLE_FILE
from app.core.guide.mapping import read_mapping_table
from app.core.messages import MessageKey
from app.core.projection.clock import split_seconds
from app.core.projection.journey_view import JourneyView, build_journey_view
from app.core.projection.master_data import MasterStatus
from app.core.projection.notices import NoticeScope
from app.core.projection.timing import OffsetOrigin, StepKind, TimeResult, TimeStatus
from tests.guide.changed import expectations
from tests.support import PROJECT_ROOT, REF_TARGETS

EX_01 = "01_NeTEx_Spiez_Interlaken_Ost.xml"
EX_08 = "08_NeTEX_CH_Bern_Olten_ZuerichHB_Winterthur_StGallen_with_Facilities.xml"
EX_15 = "15_NeTEx_CH_1026478_11957.xml"
EX_21 = "21_NeTEx_CH_Kurswagen_Zuerich_Bremen.xml"


def views(guide_path: Path, name: str) -> dict[str, JourneyView]:
    config = load_config(PROJECT_ROOT)
    data = (examples_dir(guide_path) / name).read_bytes()
    index = open_dataset([SourceFile(name, data)], config.not_relevant_elements, REF_TARGETS).index
    table = read_mapping_table(guide_path.joinpath(*MAPPING_TABLE_FILE.parts))
    journeys = index.elements_by_name(["ServiceJourney", "TemplateServiceJourney"])
    return {
        journey.xml_id: build_journey_view(index, journey, table)
        for journey in journeys
        if journey.xml_id
    }


def clock(time: TimeResult | None) -> str:
    assert time is not None
    assert time.total is not None
    day, text = split_seconds(time.total)
    return f"{text} {day:+d}"


def timetable(view: JourneyView) -> list[tuple[str, str]]:
    result = []
    for stop in view.stops:
        arrival = "-" if stop.times.arrival is None else clock(stop.times.arrival)
        departure = "-" if stop.times.departure is None else clock(stop.times.departure)
        result.append((arrival, departure))
    return result


def test_example_01_stops_and_calculated_times(guide_path: Path) -> None:
    with expectations(guide_path, EX_01):
        [view] = views(guide_path, EX_01).values()
        assert [stop.stop_point.text for stop in view.stops] == [
            "Spiez",
            "Interlaken West",
            "Interlaken Ost",
        ]
        assert timetable(view) == [
            ("-", "10:35:00 +0"),
            ("10:45:00 +0", "10:48:00 +0"),
            ("10:54:00 +0", "-"),
        ]
        last = view.stops[2].times.arrival
        assert last is not None
        assert last.status is TimeStatus.COMPUTED
        assert [(step.kind, step.value) for step in last.chain] == [
            (StepKind.DEPARTURE_TIME, "10:35:00"),
            (StepKind.DAY_OFFSET, "0"),
            (StepKind.RUN_TIME, "PT10M"),
            (StepKind.WAIT_TIME, "PT3M"),
            (StepKind.RUN_TIME, "PT6M"),
        ]
        assert all(step.element is not None for step in last.chain)
        assert [
            step.related[0].xml_id for step in last.chain if step.kind is StepKind.RUN_TIME
        ] == [
            "tl-1",
            "tl-2",
        ]
        # Kein OnwardTimingLinkRef in diesem Beispiel: Strecken über Von-/Nach-Punkt bestimmt (Z4).
        note = next(f for f in view.findings if f.key is MessageKey.TIMING_LINK_FROM_TO)
        assert note.params["legs"] == 2


def test_example_01_comment_contradicts_the_data(guide_path: Path) -> None:
    """Der Kommentar der Datei nennt 10:53, die Daten ergeben 10:54 (docs/assumptions.md)."""
    with expectations(guide_path, EX_01):
        text = (examples_dir(guide_path) / EX_01).read_text(encoding="utf-8")
        assert "10:53 Ankunft in Interlaken Ost" in text


def test_example_01_header_and_master_data(guide_path: Path) -> None:
    with expectations(guide_path, EX_01):
        [view] = views(guide_path, EX_01).values()
        assert [number.text for number in view.train_numbers] == ["99999"]
        assert view.line.text == "RE"
        assert [(c.role, c.short_name.text) for c in view.categories] == [
            ("journey", "RE"),
            ("line", "RE"),
        ]
        category = view.categories[0]
        assert [name.text for name in category.names] == ["RegioExpress"]
        assert category.master is not None
        assert category.master.status is MasterStatus.FOUND
        assert category.master.matches[0].sheet == "VMArt->NeTEx"
        assert dict(category.master.matches[0].texts)["Bezeichnung"] == "RegioExpress"
        line = view.transports[1]
        assert (line.mode.text, line.submode_type, line.submode.text) == (
            "rail",
            "RailSubmode",
            "interregionalRail",
        )


def test_example_08_offers_on_sections(guide_path: Path) -> None:
    with expectations(guide_path, EX_08):
        [view] = views(guide_path, EX_08).values()
        assert [stop.stop_point.text for stop in view.stops] == [
            "Bern",
            "Olten",
            "Zuerich_HB",
            "Winterthur",
            "St_Gallen",
        ]
        assert [stop.part_numbers for stop in view.stops] == [(1,), (1,), (2,), (2,), (2,)]
        first, second = view.parts
        assert (first.start_stop.position, first.end_stop.position) == (1, 2)
        assert (second.start_stop.position, second.end_stop.position) == (3, 5)
        for part in view.parts:
            [facility] = part.facilities
            [group] = facility.groups
            assert group.element.name == "CateringFacilityList"
            [code] = group.codes
            assert code.code == "bistro"
            assert code.master is not None
            assert code.master.status is MasterStatus.FOUND
            assert dict(code.master.matches[0].texts)["Angebotabkürzung"] == "WS"
        # Zeiten der Teilstrecken stimmen mit den berechneten Zeiten überein.
        assert MessageKey.PART_TIME_DIFFERS not in [f.key for f in view.findings]
        [whole] = view.facilities
        codes = [(g.element.name, c.code) for g in whole.groups for c in g.codes]
        assert codes == [("FareClasses", "firstClass"), ("PassengerCommsFacilityList", "freeWifi")]
        assert whole.groups[0].codes[0].master is not None
        assert whole.groups[0].codes[0].master.status is MasterStatus.FOUND
        assert whole.groups[1].codes[0].master is not None
        assert whole.groups[1].codes[0].master.status is MasterStatus.NONE


def test_example_08_notices_with_range(guide_path: Path) -> None:
    with expectations(guide_path, EX_08):
        [view] = views(guide_path, EX_08).values()
        ranges = [(n.scope, n.start_position, n.end_position) for n in view.notices]
        assert ranges == [(NoticeScope.PATTERN_REF, 1, 2), (NoticeScope.PATTERN_REF, 3, 5)]
        assert all(
            n.notice is not None and n.notice.xml_id == "ch:1:Notice:A__WS" for n in view.notices
        )
        languages = [(t.text.lang, t.text.text, t.alternative_for) for t in view.notices[0].texts]
        assert languages[0] == ("de", "Bistro", None)
        assert len(languages) == 4
        # Zwei Zuweisungen auf Frame-Ebene nennen weder Fahrt noch Fahrtmuster.
        unassigned = next(f for f in view.findings if f.key is MessageKey.NOTICE_UNASSIGNED)
        assert unassigned.params == {"count": 2}


def test_example_15_day_offset_one(guide_path: Path) -> None:
    with expectations(guide_path, EX_15):
        [view] = views(guide_path, EX_15).values()
        departure = view.stops[0].times.departure
        assert clock(departure) == "04:34:00 +1"
        assert departure is not None
        assert departure.offset_origin is OffsetOrigin.EXPLICIT
        assert [clock(stop.times.departure) for stop in view.stops[:-1]] == [
            "04:34:00 +1",
            "04:36:00 +1",
            "04:37:00 +1",
            "04:39:00 +1",
        ]
        assert clock(view.stops[-1].times.arrival) == "04:41:00 +1"
        step = departure.chain[1]
        assert (step.kind, step.value, step.default) == (StepKind.DAY_OFFSET, "1", False)
        assert step.element is not None
        assert step.element.name == "DepartureDayOffset"
        # Hier steht TimingLink im OnwardTimingLinkRef: kein Hinweis „über Von/Nach-Punkt“ nötig.
        assert (
            next(f for f in view.findings if f.key is MessageKey.TIMING_LINK_FROM_TO).params["legs"]
            == 4
        )


def test_example_21_coach_across_midnight(guide_path: Path) -> None:
    with expectations(guide_path, EX_21):
        all_views = views(guide_path, EX_21)
        coach = all_views["ch:1:ServiceJourney:KW37"]
        assert [stop.stop_point.text for stop in coach.stops] == [
            "Zürich HB",
            "Basel Bad Bf",
            "Hannover Hbf",
            "Bremen Hbf",
        ]
        assert timetable(coach) == [
            ("-", "22:15:00 +0"),
            ("23:19:00 +0", "23:40:00 +0"),
            ("06:12:00 +1", "06:44:00 +1"),
            ("07:54:00 +1", "-"),
        ]
        crossing = coach.stops[2].times.arrival
        assert crossing is not None
        assert crossing.offset_origin is OffsetOrigin.COMPUTED
        # Die Zeiten der drei Teilstrecken (mit ausdrücklichem Tag) bestätigen die Rechnung.
        assert [(p.start.total, p.end.total) for p in coach.parts] == [
            (22 * 3600 + 15 * 60, 23 * 3600 + 19 * 60),
            (23 * 3600 + 40 * 60, 24 * 3600 + 6 * 3600 + 12 * 60),
            (24 * 3600 + 6 * 3600 + 44 * 60, 24 * 3600 + 7 * 3600 + 54 * 60),
        ]
        assert [p.end.day_offset.text for p in coach.parts] == ["0", "1", "1"]
        # Die Teilstrecken verweisen auf Halte anderer Fahrtmuster: keine Zuordnung zu Halten.
        assert [p.start_stop.position for p in coach.parts] == [None, None, None]
        assert [p.start_stop.stop.text for p in coach.parts] == [
            "Zürich HB",
            "Basel Bad Bf",
            "Hannover Hbf",
        ]
        assert [p.parent_journey.text for p in coach.parts] == [
            "ch:1:ServiceJourney:472",
            "ch:1:ServiceJourney:470",
            "ch:1:ServiceJourney:2746",
        ]
        # Die anschliessende Fahrt 2746 startet 06:44 mit DepartureDayOffset 0; ihre Betriebstage
        # und die des Kurswagens sind beide alle 365 Tage des Jahres 2026.
        following = all_views["ch:1:ServiceJourney:2746"]
        assert clock(following.stops[0].times.departure) == "06:44:00 +0"
        for view in (coach, following):
            [validity] = view.validities
            assert validity.days is not None
            assert validity.days.valid_count == validity.days.period_days == 365
        keys = [f.key for f in coach.findings]
        assert MessageKey.DST_NIGHT_FORWARD in keys
        assert MessageKey.DST_NIGHT_BACK in keys
