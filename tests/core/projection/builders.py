"""Baukasten für kleine NeTEx-Dateien in den Tests der Fahrtansicht (synthetisch)."""

from __future__ import annotations

from dataclasses import dataclass, field

from app.core.dataset import SourceFile, open_dataset
from app.core.guide.mapping import MappingRow, MappingSheet, MappingTable
from app.core.index.dataset_index import DatasetIndex, ElementRow
from app.core.projection.journey_view import JourneyView, build_journey_view
from tests.support import FIXTURES_DIR, REF_TARGETS


def run(identifier: str, link: str, duration: str | None) -> str:
    """Eine `JourneyRunTime` (ohne `RunTime`, wenn `duration` fehlt)."""
    body = "" if duration is None else f"<RunTime>{duration}</RunTime>"
    return f"<JourneyRunTime id='{identifier}'><TimingLinkRef ref='{link}'/>{body}</JourneyRunTime>"


def wait(
    identifier: str, stop: str, duration: str | None, ref: str = "ScheduledStopPointRef"
) -> str:
    """Eine `JourneyWaitTime` für einen Halt (`ref` nennt das Ref-Element)."""
    body = "" if duration is None else f"<WaitTime>{duration}</WaitTime>"
    return f"<JourneyWaitTime id='{identifier}'><{ref} ref='{stop}'/>{body}</JourneyWaitTime>"


def link(identifier: str, start: str, end: str, attrs: str = "") -> str:
    """Ein `TimingLink` zwischen zwei Fahrplanpunkten."""
    return (
        f"<TimingLink id='{identifier}'><FromPointRef ref='{start}'{attrs}/>"
        f"<ToPointRef ref='{end}'{attrs}/></TimingLink>"
    )


def view_from_xml(xml: str) -> JourneyView:
    """Fahrtansicht der ersten Fahrt einer Datei aus Text."""
    return view_in(open_index(SourceFile("scenario.xml", xml.encode())))


def sheet(name: str, rows: list[dict[str, str]], first_row: int = 3) -> MappingSheet:
    return MappingSheet(
        name, first_row - 1, tuple(MappingRow(first_row + i, row) for i, row in enumerate(rows))
    )


TABLE = MappingTable(
    sheets={
        "Angebote": sheet(
            "Angebote",
            [
                {
                    "Angebotabkürzung": "1",
                    "Angebottext": "1. Klasse",
                    "Facility Value": "firstClass",
                },
                {"Angebotabkürzung": "WS", "Angebottext": "Bistro", "Facility Value": "bistro"},
                {"Angebotabkürzung": "X1", "Facility Value": "doppelt"},
                {"Angebotabkürzung": "X2", "Facility Value": "doppelt"},
            ],
        ),
        "VMArt->NeTEx": sheet(
            "VMArt->NeTEx",
            [{"Abk": "RE", "Bezeichnung": "RegioExpress", "TransportMode": "rail"}],
        ),
        "StopUse": sheet(
            "StopUse", [{"Value": "access", "Usage": "Default", "Description": "Regular value"}]
        ),
    }
)


def open_index(*sources: SourceFile) -> DatasetIndex:
    return open_dataset(list(sources), (), REF_TARGETS).index


def fixture_index(*names: str) -> DatasetIndex:
    return open_index(*(SourceFile(name, (FIXTURES_DIR / name).read_bytes()) for name in names))


def view_in(index: DatasetIndex, xml_id: str | None = None) -> JourneyView:
    journeys = index.elements_by_name(["ServiceJourney", "TemplateServiceJourney"])
    journey = journeys[0] if xml_id is None else next(j for j in journeys if j.xml_id == xml_id)
    return build_journey_view(index, journey, TABLE)


def fixture_view(name: str, xml_id: str | None = None) -> JourneyView:
    return view_in(fixture_index(name), xml_id)


def element(index: DatasetIndex, name: str, xml_id: str) -> ElementRow:
    return next(row for row in index.elements_by_name([name]) if row.xml_id == xml_id)


@dataclass
class Scenario:
    """Fahrt A, B, C mit Bausteinen, die ein Test einzeln ersetzen kann."""

    departure: str = "<DepartureTime>08:00:00</DepartureTime>"
    day_offset: str = ""
    points_extra: dict[int, str] = field(default_factory=dict)
    point_attrs: dict[int, str] = field(default_factory=dict)
    links: str = field(default_factory=lambda: link("tl-ab", "a", "b") + link("tl-bc", "b", "c"))
    runs: str = field(
        default_factory=lambda: run("r1", "tl-ab", "PT10M") + run("r2", "tl-bc", "PT15M")
    )
    waits: str = field(default_factory=lambda: wait("w1", "b", "PT2M"))
    demand_ref: str = "<TimeDemandTypeRef ref='tdt'/>"
    demand: str | None = None
    pattern_ref: str = "<ServiceJourneyPatternRef ref='sjp'/>"
    validity: str = "<validityConditions><AvailabilityConditionRef ref='ac'/></validityConditions>"
    availability: str = (
        "<AvailabilityCondition id='ac'><FromDate>2026-06-01T00:00:00</FromDate>"
        "<ToDate>2026-06-02T23:59:59</ToDate><ValidDayBits>11</ValidDayBits>"
        "</AvailabilityCondition>"
    )
    journey_extra: str = ""
    extra: str = ""

    def xml(self) -> str:
        points = "".join(
            f"<StopPointInJourneyPattern id='p{number}'{self.point_attrs.get(number, '')}>"
            f"<ScheduledStopPointRef ref='{stop}'/>"
            "<ForAlighting>true</ForAlighting><ForBoarding>true</ForBoarding>"
            f"{self.points_extra.get(number, '')}</StopPointInJourneyPattern>"
            for number, stop in enumerate("abc", start=1)
        )
        demand = self.demand
        if demand is None:
            demand = (
                f"<TimeDemandType id='tdt'><runTimes>{self.runs}</runTimes>"
                f"<waitTimes>{self.waits}</waitTimes></TimeDemandType>"
            )
        stops = "".join(
            f"<ScheduledStopPoint id='{s}'><Name>Halt {s}</Name></ScheduledStopPoint>"
            for s in "abc"
        )
        return (
            "<PublicationDelivery><dataObjects><CompositeFrame id='cf'><frames>"
            f"<ServiceFrame id='sf'>{stops}{self.links}"
            f"<ServiceJourneyPattern id='sjp'><pointsInSequence>{points}</pointsInSequence>"
            f"</ServiceJourneyPattern>{demand}</ServiceFrame>"
            f"<ServiceCalendarFrame id='cal'>{self.availability}</ServiceCalendarFrame>"
            f"<TimetableFrame id='tf'><ServiceJourney id='j'>{self.validity}{self.departure}"
            f"{self.day_offset}{self.pattern_ref}{self.demand_ref}{self.journey_extra}"
            f"</ServiceJourney>{self.extra}</TimetableFrame>"
            "</frames></CompositeFrame></dataObjects></PublicationDelivery>"
        )

    def index(self) -> DatasetIndex:
        return open_index(SourceFile("scenario.xml", self.xml().encode()))

    def view(self) -> JourneyView:
        return view_in(self.index())
