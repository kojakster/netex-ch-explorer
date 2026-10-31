from __future__ import annotations

from app.core.dataset import Dataset, SourceFile, open_dataset
from app.core.diagnostics import DiagnosticCategory
from app.core.messages import Severity
from tests.support import FIXTURES_DIR


def load(*names: str, gray: tuple[str, ...] = ()) -> Dataset:
    return open_dataset(
        [SourceFile(name, (FIXTURES_DIR / name).read_bytes()) for name in names], gray
    )


def test_files_and_object_types() -> None:
    dataset = load("ch20_network_offer.xml", "ch20_site_offer.xml")
    files = dataset.index.files()
    assert [(f.id, f.name, f.readable) for f in files] == [
        (1, "ch20_network_offer.xml", True),
        (2, "ch20_site_offer.xml", True),
    ]
    assert files[1].elements == 23
    types = dict(dataset.index.object_types())
    assert types["StopPlace"] == 3
    assert types["ScheduledStopPoint"] == 3
    assert dataset.index.file_text(2) is not None
    assert dataset.index.file_text(9) is None
    dataset.close()


def test_frames_are_assigned_to_innermost_frame() -> None:
    dataset = load("ch20_three_stops.xml")
    index = dataset.index
    frames = index.frames()
    assert [frame.name for frame in frames] == [
        "CompositeFrame",
        "ResourceFrame",
        "SiteFrame",
        "ServiceFrame",
        "ServiceCalendarFrame",
        "TimetableFrame",
    ]
    [quay] = index.objects_by_id("ch:1:sloid:SYN1:0:1", "Quay")
    frame = index.element(quay.frame_id or 0)
    assert frame is not None
    assert frame.name == "SiteFrame"
    composite = frames[0]
    assert composite.frame_id == composite.id
    root = index.element(1)
    assert root is not None
    assert root.frame_id is None
    assert root.name == "PublicationDelivery"


def test_not_relevant_is_inherited() -> None:
    dataset = load("ch20_three_stops.xml", gray=("quays",))
    [quay] = dataset.index.objects_by_id("ch:1:sloid:SYN1:0:1", "Quay")
    [point] = dataset.index.objects_by_id("ch:1:sloid:SYN1:0:1", "ScheduledStopPoint")
    assert quay.not_relevant
    assert not point.not_relevant


def test_labels_and_search() -> None:
    index = load("ch20_three_stops.xml").index
    total, rows = index.search_objects(None, "synthetisch b", 10, 0)
    assert total == 2
    assert {(row.name, row.label) for row in rows} == {
        ("StopPlace", "Synthetisch B"),
        ("ScheduledStopPoint", "Synthetisch B"),
    }
    total, rows = index.search_objects("Quay", None, 2, 1)
    assert total == 3
    assert [row.xml_id for row in rows] == ["ch:1:sloid:SYN2:0:1", "ch:1:sloid:SYN3:0:1"]
    assert index.search_objects(None, "%", 10, 0)[0] == 0
    assert index.search_objects(None, "_", 10, 0)[0] == 0
    total, _ = index.search_objects("TimingLink", "syn1-2", 10, 0)
    assert total == 1


def test_label_from_nested_text() -> None:
    data = (
        b'<PublicationDelivery><dataObjects><X id="a"><Name> <Text lang="de">Bern</Text></Name></X>'
        b'<X id="b"><Name/></X><X id="c"/></dataObjects></PublicationDelivery>'
    )
    index = open_dataset([SourceFile("t.xml", data)], ()).index
    labels = {row.xml_id: row.label for row in index.search_objects("X", None, 10, 0)[1]}
    assert labels == {"a": "Bern", "b": None, "c": None}


def test_children_descendants_and_siblings() -> None:
    index = load("ch20_three_stops.xml").index
    [stop] = index.objects_by_id("ch:1:sloid:SYN2", "StopPlace")
    assert [child.name for child in index.children(stop.id)] == ["Name", "quays"]
    assert [d.name for d in index.descendants(stop.id, 10)] == [
        "Name",
        "quays",
        "Quay",
        "PublicCode",
    ]
    assert len(index.descendants(stop.id, 2)) == 2
    assert stop.sibling_position == 2
    assert index.same_name_sibling_count(stop) == 3
    root = index.element(1)
    assert root is not None
    assert index.same_name_sibling_count(root) == 1
    assert index.element(99999) is None
    assert index.descendants(99999, 10) == []


def test_elements_without_end_keep_their_descendants() -> None:
    index = open_dataset([SourceFile("t.xml", b"<r><a><b>x</b>")], ()).index
    root, a, b = (index.element(n) for n in (1, 2, 3))
    assert root is not None and a is not None and b is not None
    assert root.end is None and a.end is None
    assert [d.name for d in index.descendants(root.id, 10)] == ["a", "b"]
    assert [d.name for d in index.descendants(a.id, 10)] == ["b"]
    assert index.descendants(b.id, 10) == []


def test_search_ignores_case_beyond_ascii() -> None:
    data = "<r><X id='a'><Name>ZÜRICH HB</Name></X><X id='b'><Name>Genève</Name></X></r>"
    index = open_dataset([SourceFile("t.xml", data.encode())], ()).index
    assert [row.xml_id for row in index.search_objects(None, "zürich", 10, 0)[1]] == ["a"]
    assert [row.xml_id for row in index.search_objects(None, "GENÈVE", 10, 0)[1]] == ["b"]
    assert index.search_objects(None, "a\nZ", 10, 0)[0] == 0


def test_line_starts_and_file_name() -> None:
    index = open_dataset([SourceFile("t.xml", b"<a>\n<b/>\n</a>")], ()).index
    assert index.line_starts(1) == [0, 4, 9]
    assert index.line_starts(1) is index.line_starts(1)
    assert index.line_starts(2) is None
    assert index.file_name(1) == "t.xml"
    assert index.file_name(2) is None


def test_elements_by_name() -> None:
    index = load("ch20_midnight.xml").index
    assert [row.xml_id for row in index.elements_by_name(["ServiceJourney"])] == [
        "ch:1:sjyid:SYN:1",
        "ch:1:sjyid:SYN:2",
    ]


def test_diagnostics_filter() -> None:
    index = load("broken_xml.xml", "ch20_three_stops.xml").index
    [item] = index.diagnostics()
    assert item.file_name == "broken_xml.xml"
    assert item.diagnostic.position is not None
    assert index.diagnostics(DiagnosticCategory.XML_SYNTAX, Severity.ERROR) == [item]
    assert index.diagnostics(DiagnosticCategory.XSD) == []
    assert index.diagnostics(severity=Severity.INFO) == []
    assert not index.files()[0].readable


def test_diagnostic_without_position() -> None:
    index = open_dataset(
        [SourceFile("t.xml", b'<?xml version="1.0" encoding="latin1"?><a/>')], ()
    ).index
    [item] = index.diagnostics()
    assert item.diagnostic.position is None
