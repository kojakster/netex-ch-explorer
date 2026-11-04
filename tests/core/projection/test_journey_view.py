from __future__ import annotations

from app.core.dataset import SourceFile
from app.core.messages import MessageKey, Severity
from app.core.projection.common import LookupStatus
from app.core.projection.journey_view import JourneyView, is_journey
from app.core.projection.master_data import MasterStatus
from app.core.projection.notices import NoticeScope
from tests.core.projection.builders import (
    Scenario,
    element,
    fixture_index,
    fixture_view,
    link,
    open_index,
    view_from_xml,
    view_in,
)


def keys(view: JourneyView) -> list[MessageKey]:
    return [finding.key for finding in view.findings]


def test_header_of_three_stops() -> None:
    view = fixture_view("ch20_three_stops.xml")
    assert [number.text for number in view.train_numbers] == ["1"]
    assert view.line.text == "Synthetische Linie"
    assert view.pattern.text == "ch:1:ServiceJourneyPattern:SYN1"
    assert view.time_demand_type.text == "ch:1:TimeDemandType:SYN1"
    assert (view.operator.status, view.operator.text) == (LookupStatus.FOUND, "Synthetische Bahn")
    assert view.operator.element is not None
    assert view.operator.element.name == "Name"
    assert [(t.role, t.mode.text, t.submode.status) for t in view.transports] == [
        ("journey", "rail", LookupStatus.ABSENT),
        ("line", "rail", LookupStatus.ABSENT),
    ]
    [category] = view.categories
    assert category.role == "journey"
    [validity] = view.validities
    assert validity.days is not None
    assert validity.days.valid_count == 5
    assert validity.days.period_days == 7
    assert [stop.stop_point.text for stop in view.stops] == [
        "Synthetisch A",
        "Synthetisch B",
        "Synthetisch C",
    ]


def test_stop_properties_and_places() -> None:
    first, second, third = fixture_view("ch20_three_stops.xml").stops
    assert (first.for_boarding.text, first.for_alighting.text) == ("true", "false")
    assert (third.for_boarding.text, third.for_alighting.text) == ("false", "true")
    assert first.for_boarding.element is not None
    assert first.for_boarding.element.name == "ForBoarding"
    assert first.request_stop.status is LookupStatus.ABSENT
    assert first.stop_use is None
    assert second.stop_place.text == "Synthetisch B"
    assert second.stop_place.element is not None
    assert second.stop_place.element.name == "Name"
    assert second.quay.text == "2"
    assert second.quay.element is not None
    assert second.quay.element.name == "PublicCode"
    assert second.assignment is not None
    assert second.assignment.xml_id == "ch:1:PassengerStopAssignment:SYN2"


def test_stops_follow_the_xml_order_not_the_order_attribute() -> None:
    scenario = Scenario(point_attrs={1: " order='3'", 2: " order='2'", 3: " order='1'"})
    view = scenario.view()
    assert [stop.stop_point.text for stop in view.stops] == ["Halt a", "Halt b", "Halt c"]
    [finding] = [f for f in view.findings if f.key is MessageKey.STOP_ORDER_DIFFERS]
    assert finding.severity is Severity.INFO


def test_order_attribute_in_sequence_gives_no_hint() -> None:
    view = Scenario(point_attrs={1: " order='1'", 2: " order='2'", 3: " order='3'"}).view()
    assert MessageKey.STOP_ORDER_DIFFERS not in keys(view)
    partial = Scenario(point_attrs={1: " order='2'", 2: " order='1'"}).view()
    assert MessageKey.STOP_ORDER_DIFFERS not in keys(partial)
    text = Scenario(point_attrs={1: " order='b'", 2: " order='a'", 3: " order='c'"}).view()
    assert MessageKey.STOP_ORDER_DIFFERS not in keys(text)


def test_stop_place_not_in_this_file() -> None:
    view = fixture_view("ch20_network_offer.xml")
    stop = view.stops[0]
    assert stop.stop_place.status is LookupStatus.EXTERNAL_OR_UNLOADED
    assert stop.stop_place.text == "ch:1:sloid:SYN1"
    assert stop.quay.status is LookupStatus.EXTERNAL_OR_UNLOADED
    assert stop.assignment is not None


def test_stop_place_resolves_with_the_site_offer() -> None:
    index = fixture_index("ch20_network_offer.xml", "ch20_site_offer.xml")
    stop = view_in(index).stops[0]
    assert stop.stop_place.text == "Synthetisch A"
    assert stop.quay.text == "1"


def test_stop_without_assignment() -> None:
    # Die Datei enthält StopPlace-Objekte, aber keine Zuordnung für Halt a.
    xml = Scenario(extra="<StopPlace id='sp'><Name>Irgendwo</Name></StopPlace>").xml()
    stop = view_from_xml(xml).stops[0]
    assert stop.stop_place.status is LookupStatus.ABSENT
    assert stop.assignment is None


def test_stop_without_assignment_and_without_stop_places_is_external() -> None:
    stop = Scenario().view().stops[0]
    assert stop.stop_place.status is LookupStatus.EXTERNAL_OR_UNLOADED
    assert stop.stop_place.text == "a"


def _assignment(identifier: str) -> str:
    return (
        f"<PassengerStopAssignment id='{identifier}'><ScheduledStopPointRef ref='a'/>"
        "</PassengerStopAssignment>"
    )


def _assignments(extra: str) -> JourneyView:
    return Scenario(extra=extra).view()


def test_several_assignments_are_ambiguous() -> None:
    both = f"{_assignment('x1')}{_assignment('x2')}"
    stop = _assignments(both).stops[0]
    assert stop.stop_place.status is LookupStatus.AMBIGUOUS
    assert stop.assignment is not None


def test_assignment_without_stop_place_or_quay() -> None:
    xml = (
        "<PassengerStopAssignment id='x1'><ScheduledStopPointRef ref='a'/>"
        "<StopPlaceRef ref='sp'/><QuayRef ref='q'/></PassengerStopAssignment>"
        "<StopPlace id='sp'/><Quay id='q'><Name>Gleis 3</Name></Quay>"
    )
    stop = _assignments(xml).stops[0]
    assert stop.stop_place.status is LookupStatus.ABSENT
    assert stop.stop_place.element is not None
    assert stop.stop_place.element.name == "StopPlace"
    assert stop.quay.text == "Gleis 3"
    stop = _assignments(_assignment("x1")).stops[0]
    assert stop.stop_place.status is LookupStatus.ABSENT
    assert stop.quay.status is LookupStatus.ABSENT


def test_offers_fixture_header() -> None:
    view = fixture_view("ch20_offers.xml")
    assert [(c.role, c.short_name.text) for c in view.categories] == [
        ("journey", "SYN"),
        ("line", "SYN"),
    ]
    category = view.categories[0]
    assert [(n.lang, n.text) for n in category.names] == [
        ("de", "Synthetischer Zug"),
        ("en", "Synthetic train"),
    ]
    assert category.master is not None
    assert category.master.status is MasterStatus.NONE
    line_transport = view.transports[1]
    assert (line_transport.submode_type, line_transport.submode.text) == (
        "RailSubmode",
        "regionalRail",
    )
    assert line_transport.submode.element is not None
    assert line_transport.submode.element.name == "RailSubmode"


def test_product_category_found_in_master_data() -> None:
    xml = Scenario(
        journey_extra="<TypeOfProductCategoryRef ref='cat'/>",
        extra="<TypeOfProductCategory id='cat'><Name>RegioExpress</Name><ShortName>RE</ShortName>"
        "</TypeOfProductCategory>",
    ).xml()
    category = view_from_xml(xml).categories[0]
    assert category.master is not None
    assert category.master.status is MasterStatus.FOUND
    assert category.master.matches[0].sheet == "VMArt->NeTEx"
    assert dict(category.master.matches[0].texts)["Bezeichnung"] == "RegioExpress"


def test_product_category_problems() -> None:
    unresolved = Scenario(journey_extra="<TypeOfProductCategoryRef ref='fehlt'/>").view()
    [category] = unresolved.categories
    assert category.target is None
    assert category.problem is not None
    assert category.problem.status is LookupStatus.EXTERNAL_OR_UNLOADED
    nameless = Scenario(
        journey_extra="<TypeOfProductCategoryRef ref='cat'/>",
        extra="<TypeOfProductCategory id='cat'/>",
    ).view()
    [category] = nameless.categories
    assert category.short_name.status is LookupStatus.ABSENT
    assert category.names == []
    assert category.master is None


def test_stop_use_and_request_stop() -> None:
    second = fixture_view("ch20_offers.xml").stops[1]
    assert second.request_stop.text == "true"
    assert second.stop_use is not None
    assert second.stop_use.code == "access"
    assert second.stop_use.element.name == "StopUse"
    assert second.stop_use.master is not None
    assert second.stop_use.master.status is MasterStatus.FOUND
    assert dict(second.stop_use.master.matches[0].texts)["Description"] == "Regular value"


def test_facilities_of_the_whole_journey_with_master_data() -> None:
    [facility] = fixture_view("ch20_offers.xml").facilities
    assert facility.facility_set is not None
    assert facility.facility_set.xml_id == "ch:1:ServiceFacilitySet:SYN-all"
    [fare, comms] = facility.groups
    assert fare.element.name == "FareClasses"
    first, second = fare.codes
    assert (first.code, second.code) == ("firstClass", "secondClass")
    assert first.master is not None
    assert first.master.status is MasterStatus.FOUND
    assert dict(first.master.matches[0].texts)["Angebottext"] == "1. Klasse"
    assert second.master is not None
    assert second.master.status is MasterStatus.NONE
    assert comms.codes[0].code == "freeWifi"


def test_facility_set_problems_and_description() -> None:
    xml = Scenario(
        journey_extra=(
            "<facilities><ServiceFacilitySetRef ref='fs'/><ServiceFacilitySetRef ref='fehlt'/>"
            "</facilities>"
        ),
        extra=(
            "<ServiceFacilitySet id='fs'><Description lang='de'>Nur 2. Klasse"
            "<Text lang='en'>2nd class only</Text></Description>"
            "<Extensions><Priority>1</Priority></Extensions>"
            "<FareClasses>secondClass</FareClasses><accommodations/></ServiceFacilitySet>"
        ),
    ).view()
    first, second = xml.facilities
    assert [(t.lang, t.text) for t in first.description] == [
        ("de", "Nur 2. Klasse"),
        ("en", "2nd class only"),
    ]
    assert [group.element.name for group in first.groups] == ["FareClasses"]
    assert second.facility_set is None
    assert second.problem is not None
    assert second.problem.status is LookupStatus.NOT_RESOLVED


def test_part_with_facilities_on_a_section() -> None:
    view = fixture_view("ch20_offers.xml")
    [part] = view.parts
    assert part.number == 1
    assert (part.start_stop.stop.text, part.start_stop.position) == ("Synthetisch A", 1)
    assert (part.end_stop.stop.text, part.end_stop.position) == ("Synthetisch B", 2)
    assert part.start.total == 8 * 3600
    assert part.end.total == 8 * 3600 + 600
    assert part.purpose.text == "Facility change"
    assert [g.codes[0].code for f in part.facilities for g in f.groups] == ["bistro"]
    assert part.facilities[0].groups[0].codes[0].master is not None
    assert part.facilities[0].groups[0].codes[0].master.status is MasterStatus.FOUND
    assert [stop.part_numbers for stop in view.stops] == [(1,), (1,), ()]
    assert MessageKey.PART_TIME_DIFFERS not in keys(view)


def _part_xml(start: str, end: str, extra: str = "", refs: str | None = None) -> str:
    refs = refs or ("<FromStopPointRef ref='a'/><ToStopPointRef ref='b'/>")
    return (
        "<parts><JourneyPart id='jp'>" + extra + refs + f"<StartTime>{start}</StartTime>"
        f"<EndTime>{end}</EndTime></JourneyPart></parts>"
    )


def test_part_time_that_contradicts_the_calculation_is_a_warning() -> None:
    view = Scenario(journey_extra=_part_xml("08:01:00", "08:11:00")).view()
    differences = [f for f in view.findings if f.key is MessageKey.PART_TIME_DIFFERS]
    assert [f.severity for f in differences] == [Severity.WARNING, Severity.WARNING]
    assert differences[0].params == {
        "part": "jp",
        "field": "StartTime",
        "stated": "08:01:00",
        "statedDay": 0,
        "computed": "08:00:00",
        "computedDay": 0,
    }
    assert differences[1].params["field"] == "EndTime"
    assert differences[0].element is not None
    assert differences[0].element.name == "StartTime"


def test_part_time_is_not_compared_with_utc_times() -> None:
    view = fixture_view("ch20_utc_departure.xml")
    assert MessageKey.PART_TIME_DIFFERS not in keys(view)
    notes = [f for f in view.findings if f.key is MessageKey.PART_TIME_UTC]
    assert [(f.severity, f.params["field"]) for f in notes] == [
        (Severity.INFO, "StartTime"),
        (Severity.INFO, "EndTime"),
    ]
    assert notes[0].element is not None
    assert notes[0].element.name == "StartTime"


def test_part_day_offset_is_compared() -> None:
    extra = "<EndTimeDayOffset>1</EndTimeDayOffset>"
    part = (
        "<parts><JourneyPart id='jp'><FromStopPointRef ref='a'/><ToStopPointRef ref='b'/>"
        "<StartTime>08:00:00</StartTime><EndTime>08:10:00</EndTime>"
        + extra
        + "</JourneyPart></parts>"
    )
    differences = [
        f
        for f in Scenario(journey_extra=part).view().findings
        if f.key is MessageKey.PART_TIME_DIFFERS
    ]
    assert [f.params["field"] for f in differences] == ["EndTime"]
    assert differences[0].params["statedDay"] == 1


def test_part_time_is_not_compared_when_unreadable_or_unplaced() -> None:
    bad = Scenario(journey_extra=_part_xml("früh", "spät")).view()
    assert MessageKey.PART_TIME_DIFFERS not in keys(bad)
    assert bad.parts[0].start.total is None
    unplaced = Scenario(
        journey_extra=_part_xml("09:00:00", "09:10:00", refs="<FromStopPointRef ref='x'/>")
    ).view()
    assert MessageKey.PART_TIME_DIFFERS not in keys(unplaced)
    assert unplaced.parts[0].start_stop.stop.status is LookupStatus.NOT_RESOLVED
    assert unplaced.parts[0].start_stop.position is None


def test_part_without_end_reaches_the_end_of_the_journey() -> None:
    part = (
        "<parts><JourneyPart id='jp'><FromStopPointRef ref='b'/>"
        "<StartTime>08:12:00</StartTime><EndTime>08:27:00</EndTime></JourneyPart></parts>"
    )
    view = Scenario(journey_extra=part).view()
    assert [stop.part_numbers for stop in view.stops] == [(), (1,), (1,)]
    assert view.parts[0].end_stop.stop.status is LookupStatus.ABSENT


def test_part_with_stop_point_in_pattern_of_this_journey() -> None:
    part = (
        "<parts><JourneyPart id='jp'><FromPointInPatternRef ref='p2'/>"
        "<ToPointInPatternRef ref='p3'/><StartTime>08:12:00</StartTime>"
        "<EndTime>08:27:00</EndTime></JourneyPart></parts>"
    )
    view = Scenario(journey_extra=part).view()
    [item] = view.parts
    assert (item.start_stop.stop.text, item.start_stop.position) == ("Halt b", 2)
    assert (item.end_stop.stop.text, item.end_stop.position) == ("Halt c", 3)
    assert MessageKey.PART_TIME_DIFFERS not in keys(view)


def test_part_on_a_stop_visited_twice_is_not_placed() -> None:
    xml = Scenario(journey_extra=_part_xml("08:00:00", "08:10:00")).xml()
    xml = xml.replace("<ScheduledStopPointRef ref='c'/>", "<ScheduledStopPointRef ref='a'/>")
    view = view_from_xml(xml)
    assert view.parts[0].start_stop.position is None
    assert view.parts[0].start_stop.stop.text == "Halt a"


def test_part_with_problems_in_references() -> None:
    part = (
        "<parts><JourneyPart id='jp'><ParentJourneyRef ref='fehlt'/>"
        "<PurposeOfJourneyPartitionRef ref='fehlt'/><TrainNumberRef ref='tn'/>"
        "<Description lang='de'>Teil</Description><StartTime>08:00:00</StartTime>"
        "<EndTime>08:10:00</EndTime></JourneyPart></parts>"
    )
    [item] = Scenario(journey_extra=part).view().parts
    # Die Datei enthält Objekte dieser Typen, aber nicht die genannten: nicht aufgelöst (Fehler).
    assert item.parent_journey.status is LookupStatus.NOT_RESOLVED
    assert item.purpose.status is LookupStatus.EXTERNAL_OR_UNLOADED
    assert item.train_numbers[0].status is LookupStatus.EXTERNAL_OR_UNLOADED
    assert [t.text for t in item.description] == ["Teil"]
    assert item.start_stop.stop.status is LookupStatus.ABSENT


def test_parent_journey_and_purpose_resolve() -> None:
    part = (
        "<parts><JourneyPart id='jp'><ParentJourneyRef ref='elter'/>"
        "<PurposeOfJourneyPartitionRef ref='zweck'/><FromStopPointRef ref='a'/>"
        "<StartTime>08:00:00</StartTime><EndTime>08:10:00</EndTime></JourneyPart></parts>"
    )
    extra = "<ServiceJourney id='elter'/><PurposeOfJourneyPartition id='zweck'/>"
    [item] = Scenario(journey_extra=part, extra=extra).view().parts
    assert item.parent_journey.text == "elter"
    assert item.purpose.status is LookupStatus.ABSENT
    assert item.purpose.element is not None
    assert item.purpose.element.name == "PurposeOfJourneyPartition"


def test_notices_by_scope() -> None:
    view = fixture_view("ch20_offers.xml")
    journey_notice, range_notice = view.notices
    assert journey_notice.scope is NoticeScope.JOURNEY
    assert journey_notice.short_code.text == "SYN1"
    assert [(t.text.lang, t.text.text) for t in journey_notice.texts] == [
        ("de", "Synthetischer Hinweis"),
        ("en", "Synthetic notice"),
    ]
    assert (journey_notice.start_position, journey_notice.end_position) == (None, None)
    assert range_notice.scope is NoticeScope.PATTERN_REF
    assert (range_notice.start_position, range_notice.end_position) == (2, 3)
    unassigned = [f for f in view.findings if f.key is MessageKey.NOTICE_UNASSIGNED]
    assert [f.params for f in unassigned] == [{"count": 1}]
    assert unassigned[0].severity is Severity.INFO
    assert unassigned[0].element is None


def test_notices_embedded_in_pattern_and_referencing_the_journey() -> None:
    extra = (
        "<Notice id='n1'><Text lang='de'>Eins</Text><alternativeTexts>"
        "<AlternativeText attributeName='Text'><Text lang='fr'>Un</Text></AlternativeText>"
        "</alternativeTexts><TypeOfNoticeRef ref='ton'/></Notice>"
        "<TypeOfNotice id='ton'><Name>Angebot</Name></TypeOfNotice>"
        "<noticeAssignments>"
        "<NoticeAssignment id='na1'><NoticeRef ref='n1'/><ServiceJourneyRef ref='j'/>"
        "<StartPointInPatternRef ref='fremd'/></NoticeAssignment>"
        "<NoticeAssignment id='na2'><NoticeRef ref='fehlt'/>"
        "<NoticedObjectRef ref='j' nameOfRefClass='ServiceJourney'/>"
        "</NoticeAssignment></noticeAssignments>"
    )
    xml = (
        Scenario(extra=extra)
        .xml()
        .replace(
            "</pointsInSequence>",
            "</pointsInSequence><noticeAssignments><NoticeAssignment id='na0'><NoticeRef ref='n1'/>"
            "</NoticeAssignment></noticeAssignments>",
        )
    )
    pattern, journey_ref, noticed = view_from_xml(xml).notices
    assert pattern.scope is NoticeScope.PATTERN
    assert journey_ref.scope is NoticeScope.JOURNEY_REF
    assert [(t.text.lang, t.alternative_for) for t in journey_ref.texts] == [
        ("de", None),
        ("fr", "Text"),
    ]
    assert journey_ref.notice_type.text == "Angebot"
    assert journey_ref.start_ref is not None
    assert journey_ref.start_position is None
    assert noticed.notice is None
    assert noticed.problem is not None
    assert noticed.problem.status is LookupStatus.NOT_RESOLVED


def test_notice_without_texts_and_validity() -> None:
    extra = (
        "<Notice id='n1'><TypeOfNoticeRef ref='ton'/></Notice><TypeOfNotice id='ton'/>"
        "<noticeAssignments><NoticeAssignment id='na1'><validityConditions>"
        "<AvailabilityConditionRef ref='ac'/></validityConditions><NoticeRef ref='n1'/>"
        "<ServiceJourneyRef ref='j'/></NoticeAssignment></noticeAssignments>"
    )
    [notice] = Scenario(extra=extra).view().notices
    assert notice.texts == []
    assert notice.notice_type.status is LookupStatus.ABSENT
    assert notice.validity[0].days is not None


def test_private_codes_and_template_journey() -> None:
    xml = Scenario(
        journey_extra=(
            "<privateCodes><PrivateCode type='sjyid'>ch:1:sjyid:1</PrivateCode>"
            "<PrivateCode type='rn'> </PrivateCode></privateCodes>"
        )
    ).xml()
    [code] = view_from_xml(xml).private_codes
    assert (code.code_type, code.value) == ("sjyid", "ch:1:sjyid:1")
    template = xml.replace("ServiceJourney id='j'", "TemplateServiceJourney id='j'").replace(
        "</ServiceJourney>", "</TemplateServiceJourney>"
    )
    index = open_index(SourceFile("t.xml", template.encode()))
    journey = index.elements_by_name(["TemplateServiceJourney"])[0]
    assert is_journey(journey)
    assert not is_journey(element(index, "ServiceJourneyPattern", "sjp"))


def _dst_view(departure: str, offset: str, month_day: tuple[str, str]) -> JourneyView:
    first, second = month_day
    availability = (
        f"<AvailabilityCondition id='ac'><FromDate>{first}T00:00:00</FromDate>"
        f"<ToDate>{second}T23:59:59</ToDate><ValidDayBits>10</ValidDayBits>"
        "</AvailabilityCondition>"
    )
    return Scenario(
        departure=f"<DepartureTime>{departure}</DepartureTime>",
        day_offset=offset,
        availability=availability,
    ).view()


def test_dst_night_hint_spring_and_autumn() -> None:
    offset = "<DepartureDayOffset>1</DepartureDayOffset>"
    spring = _dst_view("01:50:00", offset, ("2026-03-28", "2026-03-29"))
    [hint] = [f for f in spring.findings if f.key is MessageKey.DST_NIGHT_FORWARD]
    assert hint.params == {"date": "2026-03-29"}
    assert hint.severity is Severity.INFO
    autumn = _dst_view("01:50:00", offset, ("2026-10-24", "2026-10-25"))
    [hint] = [f for f in autumn.findings if f.key is MessageKey.DST_NIGHT_BACK]
    assert hint.params == {"date": "2026-10-25"}


def test_utc_times_are_left_out_of_the_time_change_night_check() -> None:
    offset = "<DepartureDayOffset>1</DepartureDayOffset>"
    local = _dst_view("01:50:00", offset, ("2026-10-24", "2026-10-25"))
    assert MessageKey.DST_NIGHT_BACK in keys(local)
    utc = _dst_view("01:50:00Z", offset, ("2026-10-24", "2026-10-25"))
    assert MessageKey.DST_NIGHT_BACK not in keys(utc)
    assert MessageKey.TIME_UTC in keys(utc)


def test_no_dst_hint_when_the_journey_ends_before_two_o_clock() -> None:
    view = _dst_view("23:50:00", "", ("2026-03-28", "2026-03-29"))
    assert not any("dst" in key for key in keys(view))


def test_no_dst_hint_without_operating_days() -> None:
    view = Scenario(validity="", departure="<DepartureTime>23:50:00</DepartureTime>").view()
    assert view.validities == []
    assert not any("dst" in key for key in keys(view))


def test_availability_problems_appear_as_findings() -> None:
    availability = (
        "<AvailabilityCondition id='ac'><FromDate>2026-06-01</FromDate>"
        "<ToDate>2026-06-02</ToDate><ValidDayBits>1</ValidDayBits></AvailabilityCondition>"
    )
    view = Scenario(availability=availability).view()
    [finding] = [f for f in view.findings if f.key is MessageKey.AVAILABILITY_BITS_LENGTH]
    assert finding.element is not None
    assert finding.element.name == "ValidDayBits"


def test_pattern_and_demand_lookups() -> None:
    view = Scenario(pattern_ref="<ServiceJourneyPatternRef ref='fehlt'/>").view()
    assert view.stops == []
    assert view.pattern.status is LookupStatus.NOT_RESOLVED
    assert view.line.status is LookupStatus.ABSENT


def test_notice_embedded_in_a_stop_applies_to_that_stop() -> None:
    xml = Scenario(
        extra="<Notice id='n1'><Text lang='de'>Nur hier</Text></Notice>",
        points_extra={
            2: "<noticeAssignments><NoticeAssignment id='na1'><NoticeRef ref='n1'/>"
            "</NoticeAssignment></noticeAssignments>"
        },
    ).xml()
    [notice] = view_from_xml(xml).notices
    assert notice.scope is NoticeScope.STOP
    assert (notice.start_position, notice.end_position) == (2, 2)
    assert notice.texts[0].text.text == "Nur hier"


def test_part_whose_end_cannot_be_placed_covers_no_stop() -> None:
    refs = "<FromStopPointRef ref='a'/><ToStopPointRef ref='fehlt'/>"
    view = Scenario(journey_extra=_part_xml("08:00:00", "08:10:00", refs=refs)).view()
    assert view.parts[0].start_stop.position == 1
    assert view.parts[0].end_stop.position is None
    assert [stop.part_numbers for stop in view.stops] == [(), (), ()]


def test_part_on_single_days() -> None:
    part = (
        "<parts><JourneyPart id='jp'><validityConditions><AvailabilityConditionRef ref='ac'/>"
        "</validityConditions><FromStopPointRef ref='a'/><ToStopPointRef ref='b'/>"
        "<StartTime>08:00:00</StartTime><EndTime>08:10:00</EndTime></JourneyPart></parts>"
    )
    [item] = Scenario(journey_extra=part).view().parts
    [validity] = item.validity
    assert validity.days is not None
    assert [day.isoformat() for day in validity.days.days] == ["2026-06-01", "2026-06-02"]


def test_assignment_is_found_among_many_references_to_the_stop_point() -> None:
    # Über hundert andere Verweise auf den Fahrplanpunkt stehen vor der Zuordnung in der Datei.
    many = "".join(link(f"tl-x{number}", "a", "c") for number in range(150))
    scenario = Scenario(
        links=many + link("tl-ab", "a", "b") + link("tl-bc", "b", "c"),
        extra=(
            "<PassengerStopAssignment id='x1'><ScheduledStopPointRef ref='a'/>"
            "<StopPlaceRef ref='sp'/></PassengerStopAssignment>"
            "<StopPlace id='sp'><Name>Bern</Name></StopPlace>"
        ),
    )
    stop = scenario.view().stops[0]
    assert stop.assignment is not None
    assert stop.assignment.xml_id == "x1"
    assert stop.stop_place.text == "Bern"


def test_notices_of_a_journey_are_not_cut_off_at_five_hundred() -> None:
    extra = (
        "<Notice id='n1'/><noticeAssignments>"
        + "".join(
            f"<NoticeAssignment id='na{number:04d}'><NoticeRef ref='n1'/>"
            "<ServiceJourneyRef ref='j'/></NoticeAssignment>"
            for number in range(520)
        )
        + "</noticeAssignments>"
    )
    notices = Scenario(extra=extra).view().notices
    assert len(notices) == 520
    assert notices[-1].assignment.xml_id == "na0519"


def test_notice_without_end_point_ends_at_the_start_point() -> None:
    extra = (
        "<Notice id='n1'/><noticeAssignments>"
        "<NoticeAssignment id='na1'><NoticeRef ref='n1'/><ServiceJourneyRef ref='j'/>"
        "<StartPointInPatternRef ref='p2'/></NoticeAssignment>"
        "<NoticeAssignment id='na2'><NoticeRef ref='n1'/><ServiceJourneyRef ref='j'/>"
        "<StartPointInPatternRef ref='p1'/><EndPointInPatternRef ref='p3'/></NoticeAssignment>"
        "</noticeAssignments>"
    )
    single, span = Scenario(extra=extra).view().notices
    assert (single.start_position, single.end_position) == (2, 2)
    assert single.end_ref is None
    assert (span.start_position, span.end_position) == (1, 3)


def test_operator_is_absent_without_reference() -> None:
    assert Scenario().view().operator.status is LookupStatus.ABSENT


def test_operator_name_comes_from_the_file() -> None:
    scenario = Scenario(
        journey_extra="<OperatorRef ref='op'/>",
        extra="<Operator id='op'><Name>Betreiber Test</Name></Operator>",
    )
    operator = scenario.view().operator
    assert (operator.status, operator.text) == (LookupStatus.FOUND, "Betreiber Test")


def test_operator_without_name_keeps_the_object_as_source() -> None:
    scenario = Scenario(journey_extra="<OperatorRef ref='op'/>", extra="<Operator id='op'/>")
    operator = scenario.view().operator
    assert operator.status is LookupStatus.ABSENT
    assert operator.element is not None
    assert operator.element.name == "Operator"


def test_operator_reference_without_target_gives_the_reason() -> None:
    scenario = Scenario(
        journey_extra="<OperatorRef ref='nirgends'/>",
        extra="<Operator id='op'><Name>X</Name></Operator>",
    )
    operator = scenario.view().operator
    assert (operator.status, operator.text) == (LookupStatus.NOT_RESOLVED, "nirgends")


def test_operator_reference_ignores_an_object_of_another_type_with_the_same_id() -> None:
    """Aufgelöst wird über (ID, Typ): eine `Authority` mit derselben ID ist kein Betreiber."""
    scenario = Scenario(
        journey_extra="<OperatorRef ref='op'/>",
        extra="<Authority id='op'><Name>Falsch</Name></Authority><Operator id='anderer'/>",
    )
    operator = scenario.view().operator
    assert (operator.status, operator.text) == (LookupStatus.NOT_RESOLVED, "op")
