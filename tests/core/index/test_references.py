from __future__ import annotations

from app.core.dataset import SourceFile, open_dataset
from app.core.index.dataset_index import DatasetIndex, ElementRow
from app.core.index.references import ResolveStatus, expected_type, resolve
from tests.support import FIXTURES_DIR


def index_of(*names: str) -> DatasetIndex:
    sources = [SourceFile(name, (FIXTURES_DIR / name).read_bytes()) for name in names]
    return open_dataset(sources, ()).index


def ref_elements(index: DatasetIndex, name: str, ref: str) -> list[ElementRow]:
    root = index.element(1)
    assert root is not None
    return [
        row
        for row in index.descendants(root.id, 10_000)
        if row.name == name and row.attributes.get("ref") == ref
    ]


def test_quay_and_scheduled_stop_point_with_same_id() -> None:
    index = index_of("ch20_three_stops.xml")
    [quay_ref] = ref_elements(index, "QuayRef", "ch:1:sloid:SYN1:0:1")
    result = resolve(index, quay_ref)
    assert result.status is ResolveStatus.RESOLVED
    assert result.target is not None
    assert result.target.name == "Quay"


def test_name_of_ref_class() -> None:
    index = index_of("ch20_three_stops.xml")
    from_ref = ref_elements(index, "FromPointRef", "ch:1:sloid:SYN1:0:1")[0]
    assert expected_type(from_ref) == "ScheduledStopPoint"
    result = resolve(index, from_ref)
    assert result.target is not None
    assert result.target.name == "ScheduledStopPoint"


def test_ambiguous_target() -> None:
    index = index_of("ch20_duplicate_id.xml")
    refs = ref_elements(index, "ScheduledStopPointRef", "ch:1:sloid:SYN2:0:1")
    assert refs
    assert resolve(index, refs[0]).status is ResolveStatus.AMBIGUOUS


def test_unknown_target_and_non_reference() -> None:
    index = index_of("ch20_unresolved_ref.xml")
    [missing] = ref_elements(index, "ScheduledStopPointRef", "ch:1:sloid:SYN9:0:1")
    assert resolve(index, missing).status is ResolveStatus.NOT_FOUND
    root = index.element(1)
    assert root is not None
    assert expected_type(root) is None
    assert resolve(index, root).status is ResolveStatus.NOT_FOUND
