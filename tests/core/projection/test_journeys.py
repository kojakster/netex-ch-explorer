from __future__ import annotations

import pytest

from app.core.dataset import SourceFile, open_dataset
from app.core.index.dataset_index import DatasetIndex, ResolveResult
from app.core.index.references import ResolveStatus
from app.core.projection.common import LookupStatus
from app.core.projection.journeys import list_journeys
from tests.support import FIXTURES_DIR, REF_TARGETS


def index_of(*names: str) -> DatasetIndex:
    sources = [SourceFile(name, (FIXTURES_DIR / name).read_bytes()) for name in names]
    return open_dataset(sources, (), REF_TARGETS).index


def test_resolved_reference_without_target_is_a_program_error(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    index = open_dataset(
        [
            SourceFile(
                "t",
                b"<R><ServiceJourney id='j'>"
                b"<ServiceJourneyPatternRef ref='p'/></ServiceJourney></R>",
            )
        ],
        (),
        REF_TARGETS,
    ).index
    monkeypatch.setattr(
        DatasetIndex, "resolve", lambda _self, _ref: ResolveResult(ResolveStatus.RESOLVED)
    )
    with pytest.raises(RuntimeError, match="Ziel fehlt"):
        list_journeys(index)


def test_three_stops() -> None:
    [journey] = list_journeys(index_of("ch20_three_stops.xml"))
    assert journey.element.xml_id == "ch:1:sjyid:SYN:1"
    assert [(n.status, n.text) for n in journey.train_numbers] == [(LookupStatus.FOUND, "1")]
    assert journey.departure_time.text == "08:00:00"
    assert journey.departure_day_offset.text == "0"
    assert (journey.line.status, journey.line.text) == (LookupStatus.FOUND, "Synthetische Linie")
    assert journey.first_stop.text == "Synthetisch A"
    assert journey.last_stop.text == "Synthetisch C"
    assert journey.first_stop.element is not None
    assert journey.first_stop.element.name == "Name"
    assert (journey.category.status, journey.category.text) == (LookupStatus.FOUND, "SYN")
    assert journey.category.element is not None
    assert journey.category.element.name == "ShortName"


def test_category_absent_without_reference() -> None:
    [journey] = list_journeys(index_of("ch20_calls.xml"))
    assert journey.category.status is LookupStatus.ABSENT


def test_category_reference_without_target() -> None:
    index = open_dataset(
        [
            SourceFile(
                "t",
                b"<R><ServiceJourney id='j'><TypeOfProductCategoryRef ref='x'/>"
                b"</ServiceJourney><TypeOfProductCategory id='y'/></R>",
            )
        ],
        (),
        REF_TARGETS,
    ).index
    [journey] = list_journeys(index)
    assert journey.category.status is LookupStatus.NOT_RESOLVED
    assert journey.category.text == "x"


def test_midnight_without_day_offset() -> None:
    first, second = list_journeys(index_of("ch20_midnight.xml"))
    assert first.departure_day_offset.status is LookupStatus.ABSENT
    assert second.departure_day_offset.text == "1"
    assert [n.text for n in second.train_numbers] == ["2"]


def test_unresolved_last_stop() -> None:
    [journey] = list_journeys(index_of("ch20_unresolved_ref.xml"))
    assert journey.last_stop.status is LookupStatus.NOT_RESOLVED
    assert journey.last_stop.text == "ch:1:sloid:SYN9:0:1"


def test_network_offer_alone_and_with_site_offer() -> None:
    [alone] = list_journeys(index_of("ch20_network_offer.xml"))
    assert alone.first_stop.text == "Synthetisch A"
    [both] = list_journeys(index_of("ch20_network_offer.xml", "ch20_site_offer.xml"))
    assert both.line.text == "Synthetische Linie"


def test_missing_parts_are_marked() -> None:
    data = b"""<PublicationDelivery><dataObjects>
      <ServiceJourney id="j1"><ServiceJourneyPatternRef ref="fehlt"/>
        <trainNumbers><TrainNumberRef ref="tn-fehlt"/></trainNumbers></ServiceJourney>
      <ServiceJourney id="j2"/>
      <ServiceJourney id="j3"><ServiceJourneyPatternRef ref="p3"/></ServiceJourney>
      <ServiceJourneyPattern id="p3"><RouteView><LineRef ref="l3"/></RouteView>
        <pointsInSequence><StopPointInJourneyPattern id="s1">
          <ScheduledStopPointRef ref="ssp"/></StopPointInJourneyPattern></pointsInSequence>
      </ServiceJourneyPattern>
      <Line id="l3"/><ScheduledStopPoint id="ssp"/>
      <TemplateServiceJourney id="t1"><trainNumbers><TrainNumberRef ref="tn"/></trainNumbers>
      </TemplateServiceJourney><TrainNumber id="tn"/>
      <ServiceJourney id="j4"><ServiceJourneyPatternRef ref="p4"/></ServiceJourney>
      <ServiceJourneyPattern id="p4"><RouteView><LineRef ref="l4"/></RouteView>
      </ServiceJourneyPattern>
      <Line id="l4"><Name>Linie vier</Name></Line>
    </dataObjects></PublicationDelivery>"""
    journeys = {
        j.element.xml_id: j
        for j in list_journeys(open_dataset([SourceFile("t", data)], (), REF_TARGETS).index)
    }
    assert journeys["j1"].line.status is LookupStatus.NOT_RESOLVED
    assert journeys["j1"].train_numbers[0].status is LookupStatus.NOT_RESOLVED
    assert journeys["j2"].line.status is LookupStatus.ABSENT
    assert journeys["j2"].train_numbers == []
    assert journeys["j2"].departure_time.status is LookupStatus.ABSENT
    assert journeys["j3"].line.status is LookupStatus.ABSENT
    assert journeys["j3"].line.element is not None
    assert journeys["j3"].first_stop.status is LookupStatus.ABSENT
    assert journeys["j3"].first_stop.element is not None
    assert journeys["t1"].element.name == "TemplateServiceJourney"
    assert journeys["t1"].train_numbers[0].status is LookupStatus.ABSENT
    assert journeys["t1"].train_numbers[0].element is not None
    assert journeys["j4"].line.text == "Linie vier"
    assert journeys["j4"].first_stop.status is LookupStatus.ABSENT
