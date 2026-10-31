from __future__ import annotations

from app.core.dataset import SourceFile, open_dataset
from app.core.index.dataset_index import DatasetIndex
from app.core.provenance import LinkKind, provenance_chain
from tests.support import FIXTURES_DIR, REF_TARGETS, objects_by_id


def load(*names: str) -> DatasetIndex:
    sources = [SourceFile(n, (FIXTURES_DIR / n).read_bytes()) for n in names]
    return open_dataset(sources, (), REF_TARGETS).index


def test_chain_of_a_property_runs_from_frame_through_objects() -> None:
    index = load("ch20_three_stops.xml")
    [stop] = objects_by_id(index, "ch:1:sloid:SYN1", "StopPlace")
    [name] = [c for c in index.children(stop.id) if c.name == "Name"]
    chain = provenance_chain(index, name.id)
    assert chain is not None
    assert [(link.kind, link.element.name) for link in chain] == [
        (LinkKind.FRAME, "SiteFrame"),
        (LinkKind.OBJECT, "StopPlace"),
        (LinkKind.ELEMENT, "Name"),
    ]


def test_chain_of_an_object_and_a_frame() -> None:
    index = load("ch20_three_stops.xml")
    [quay] = objects_by_id(index, "ch:1:sloid:SYN1:0:1", "Quay")
    chain = provenance_chain(index, quay.id)
    assert chain is not None
    assert [(link.kind, link.element.name) for link in chain] == [
        (LinkKind.FRAME, "SiteFrame"),
        (LinkKind.OBJECT, "StopPlace"),
        (LinkKind.OBJECT, "Quay"),
    ]
    [frame] = [f for f in index.frames() if f.name == "SiteFrame"]
    only_frame = provenance_chain(index, frame.id)
    assert only_frame is not None
    assert [(link.kind, link.element.name) for link in only_frame] == [
        (LinkKind.FRAME, "SiteFrame")
    ]


def test_chain_of_a_reference_ends_at_its_target() -> None:
    index = load("ch20_three_stops.xml")
    [ref] = [
        row
        for row in index.descendants(1, 10_000)
        if row.name == "QuayRef" and row.attributes["ref"] == "ch:1:sloid:SYN1:0:1"
    ]
    chain = provenance_chain(index, ref.id)
    assert chain is not None
    last = chain[-1]
    assert (last.kind, last.element.name) == (LinkKind.TARGET, "Quay")
    assert chain[-2].element.id == ref.id
    assert chain[0].kind is LinkKind.FRAME


def test_chain_of_an_unresolved_reference_has_no_target() -> None:
    index = load("ch20_unresolved_ref.xml")
    [ref] = [
        r for r in index.descendants(1, 10_000) if r.attributes.get("ref") == "ch:1:sloid:SYN9:0:1"
    ]
    chain = provenance_chain(index, ref.id)
    assert chain is not None
    assert chain[-1].element.id == ref.id
    assert all(link.kind is not LinkKind.TARGET for link in chain)


def test_chain_outside_any_frame_and_unknown_element() -> None:
    index = load("ch20_three_stops.xml")
    root = provenance_chain(index, 1)
    assert root is not None
    assert [(link.kind, link.element.name) for link in root] == [
        (LinkKind.ELEMENT, "PublicationDelivery")
    ]
    assert provenance_chain(index, 10**9) is None
