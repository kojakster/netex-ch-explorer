from __future__ import annotations

import pytest

from app.core.config import load_config
from app.core.dataset import SourceFile, open_dataset
from app.core.diagnostics import DiagnosticCategory
from app.core.index.dataset_index import DatasetIndex, ElementRow
from app.core.index.references import (
    Candidate,
    ResolveStatus,
    classify,
    expected_types,
    is_reference,
    reference_version,
    resolve,
)
from app.core.messages import MessageKey, Severity
from tests.support import FIXTURES_DIR, PROJECT_ROOT

TARGETS = load_config(PROJECT_ROOT).ref_targets


def index_of(*names: str) -> DatasetIndex:
    sources = [SourceFile(name, (FIXTURES_DIR / name).read_bytes()) for name in names]
    return open_dataset(sources, (), TARGETS).index


def index_of_text(*documents: str) -> DatasetIndex:
    sources = [SourceFile(f"d{n}.xml", text.encode()) for n, text in enumerate(documents)]
    return open_dataset(sources, (), TARGETS).index


def element_name(index: DatasetIndex, element_id: int) -> str:
    element = index.element(element_id)
    assert element is not None
    return element.name


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
    [point_ref] = ref_elements(index, "ScheduledStopPointRef", "ch:1:sloid:SYN1:0:1")[:1]
    point = resolve(index, point_ref).target
    assert point is not None
    assert point.name == "ScheduledStopPoint"
    assert point.id != result.target.id


def test_name_of_ref_class() -> None:
    index = index_of("ch20_three_stops.xml")
    from_ref = ref_elements(index, "FromPointRef", "ch:1:sloid:SYN1:0:1")[0]
    assert expected_types(from_ref.name, from_ref.attributes, {}) == ("ScheduledStopPoint",)
    result = resolve(index, from_ref)
    assert result.target is not None
    assert result.target.name == "ScheduledStopPoint"


def test_expected_types_order() -> None:
    assert expected_types("LineRef", {"ref": "x"}, {}) == ("Line",)
    assert expected_types("MainLineRef", {"ref": "x"}, {"MainLineRef": ("Line",)}) == ("Line",)
    # `nameOfRefClass` geht der Liste vor, die Liste dem Namen.
    attributes = {"ref": "x", "nameOfRefClass": "Quay"}
    assert expected_types("MainLineRef", attributes, {"MainLineRef": ("Line",)}) == ("Quay",)
    assert expected_types("Name", {"ref": "x"}, {}) == ()
    assert expected_types("Ref", {"ref": "x"}, {}) == ()
    assert expected_types("LineRef", {}, {}) == ()
    assert expected_types("LineRef", {"ref": ""}, {}) == ()


def test_is_reference_and_version() -> None:
    assert is_reference("LineRef", {"ref": "a"})
    assert is_reference("Anything", {"ref": "a", "nameOfRefClass": "Line"})
    assert not is_reference("Line", {"ref": "a"})
    assert reference_version({"version": "2"}) == "2"
    assert reference_version({"versionRef": "3"}) == "3"
    assert reference_version({}) is None


def test_ref_targets_resolve_role_names() -> None:
    index = index_of_text(
        "<R><Operator id='o1' version='1'/><TimingLink id='t1' version='1'/>"
        "<ResponsibleOrganisationRef ref='o1'/><OnwardTimingLinkRef ref='t1'/></R>"
    )
    [organisation] = ref_elements(index, "ResponsibleOrganisationRef", "o1")
    [link] = ref_elements(index, "OnwardTimingLinkRef", "t1")
    assert resolve(index, organisation).status is ResolveStatus.RESOLVED
    assert resolve(index, link).status is ResolveStatus.RESOLVED
    assert index.diagnostics() == []


def test_ambiguous_target() -> None:
    index = index_of("ch20_duplicate_id.xml")
    refs = ref_elements(index, "ScheduledStopPointRef", "ch:1:sloid:SYN2:0:1")
    assert refs
    result = resolve(index, refs[0])
    assert result.status is ResolveStatus.AMBIGUOUS
    assert result.target is None
    diagnostics = [
        d for d in index.diagnostics() if d.diagnostic.key is MessageKey.REFERENCE_AMBIGUOUS
    ]
    assert diagnostics
    assert all(d.diagnostic.severity is Severity.WARNING for d in diagnostics)


def test_unresolved_when_type_exists_is_an_error() -> None:
    index = index_of("ch20_unresolved_ref.xml")
    [missing] = ref_elements(index, "ScheduledStopPointRef", "ch:1:sloid:SYN9:0:1")
    assert resolve(index, missing).status is ResolveStatus.UNRESOLVED
    [item] = index.diagnostics(DiagnosticCategory.REFERENCE)
    assert item.diagnostic.severity is Severity.ERROR
    assert item.diagnostic.key is MessageKey.REFERENCE_UNRESOLVED
    assert item.diagnostic.params == {
        "element": "ScheduledStopPointRef",
        "ref": "ch:1:sloid:SYN9:0:1",
        "expected": "ScheduledStopPoint",
    }
    assert item.diagnostic.position is not None
    assert item.diagnostic.position.line == missing.start.line


def test_external_or_unloaded_across_files() -> None:
    alone = index_of("ch20_network_offer.xml")
    [stop_place] = ref_elements(alone, "StopPlaceRef", "ch:1:sloid:SYN1")
    assert resolve(alone, stop_place).status is ResolveStatus.EXTERNAL_OR_UNLOADED
    notes = alone.diagnostics(DiagnosticCategory.REFERENCE)
    assert notes
    assert {n.diagnostic.severity for n in notes} == {Severity.INFO}
    assert {n.diagnostic.key for n in notes} == {MessageKey.REFERENCE_EXTERNAL_OR_UNLOADED}

    together = index_of("ch20_network_offer.xml", "ch20_site_offer.xml")
    [stop_place] = ref_elements(together, "StopPlaceRef", "ch:1:sloid:SYN1")
    result = resolve(together, stop_place)
    assert result.status is ResolveStatus.RESOLVED
    assert result.target is not None
    assert result.target.file_name == "ch20_site_offer.xml"
    assert together.diagnostics(DiagnosticCategory.REFERENCE) == []


def test_references_in_extensions_are_found() -> None:
    index = index_of_text(
        "<R><Line id='l1' version='1'/>"
        "<Extensions><LineRef ref='l1' version='1'/><LineRef ref='gone' version='1'/></Extensions>"
        "</R>"
    )
    [found] = ref_elements(index, "LineRef", "l1")
    assert resolve(index, found).status is ResolveStatus.RESOLVED
    [missing] = ref_elements(index, "LineRef", "gone")
    assert resolve(index, missing).status is ResolveStatus.UNRESOLVED


def test_version_decides_between_candidates() -> None:
    document = (
        "<R><Line id='l' version='1'/><Line id='l' version='2'/>"
        "<LineRef ref='l' version='2'/><LineRef ref='l' versionRef='1'/>"
        "<LineRef ref='l' version='any'/><LineRef ref='l'/></R>"
    )
    index = index_of_text(document)
    refs = [row for row in index.descendants(1, 100) if row.name == "LineRef"]
    results = [resolve(index, ref) for ref in refs]
    assert [r.status for r in results] == [
        ResolveStatus.RESOLVED,
        ResolveStatus.RESOLVED,
        ResolveStatus.AMBIGUOUS,
        ResolveStatus.AMBIGUOUS,
    ]
    assert [r.target.version if r.target else None for r in results[:2]] == ["2", "1"]


def test_classify() -> None:
    assert classify([], None, True) == (ResolveStatus.UNRESOLVED, None)
    assert classify([], None, False) == (ResolveStatus.EXTERNAL_OR_UNLOADED, None)
    assert classify([Candidate(5, "1")], "9", True) == (ResolveStatus.RESOLVED, 5)
    two = [Candidate(5, "1"), Candidate(6, "2")]
    assert classify(two, "3", True) == (ResolveStatus.AMBIGUOUS, None)
    assert classify(two, "2", True) == (ResolveStatus.RESOLVED, 6)


def test_non_reference_elements_are_not_resolved() -> None:
    index = index_of("ch20_three_stops.xml")
    root = index.element(1)
    assert root is not None
    assert resolve(index, root).status is ResolveStatus.UNRESOLVED
    assert index.reference(root.id) is None


def test_outgoing_and_incoming_references() -> None:
    index = index_of("ch20_three_stops.xml")
    [quay] = index.objects_by_id("ch:1:sloid:SYN1:0:1", "Quay")
    incoming = index.references_to(quay.id, 100)
    assert incoming
    assert {element_name(index, row.element_id) for row in incoming} == {"QuayRef"}
    assert all(row.target_id == quay.id for row in incoming)
    [journey] = index.elements_by_name(["ServiceJourney"])
    outgoing = index.references_of(journey.id, 100)
    assert "ServiceJourneyPatternRef" in {element_name(index, row.element_id) for row in outgoing}
    assert all(row.owner_id == journey.id for row in outgoing)
    assert index.references_of(journey.id, 1) == outgoing[:1]
    assert index.references_among([]) == {}


@pytest.mark.parametrize("name", sorted(TARGETS))
def test_listed_targets_differ_from_name_default(name: str) -> None:
    """Die Liste enthält nur Abweichungen vom Namen ohne `Ref`."""
    assert TARGETS[name] != (name.removesuffix("Ref"),)
