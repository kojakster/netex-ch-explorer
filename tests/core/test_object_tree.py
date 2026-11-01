from __future__ import annotations

from app.core.dataset import Dataset, SourceFile, open_dataset
from app.core.object_tree import TreeEntry, build_object_tree
from tests.support import FIXTURES_DIR, REF_TARGETS


def load(*names: str) -> Dataset:
    return open_dataset(
        [SourceFile(name, (FIXTURES_DIR / name).read_bytes()) for name in names], (), REF_TARGETS
    )


def shape(entries: list[TreeEntry]) -> list[tuple[str, int, bool]]:
    return [(e.element.name, e.depth, e.matches) for e in entries]


def test_tree_nests_frames_and_objects() -> None:
    index = load("ch20_three_stops.xml").index
    tree = build_object_tree(index, None, None)
    names = [entry.element.name for entry in tree.entries]
    assert names[:2] == ["CompositeFrame", "ResourceFrame"]
    assert tree.outside == []
    assert tree.total == tree.shown == len(tree.entries)
    assert not tree.truncated
    depths = {entry.element.name: entry.depth for entry in tree.entries}
    assert depths["CompositeFrame"] == 0
    assert depths["SiteFrame"] == 1
    assert depths["StopPlace"] == 2
    assert depths["Quay"] == 3
    assert all(entry.matches for entry in tree.entries)


def test_filter_keeps_ancestors_as_context() -> None:
    index = load("ch20_three_stops.xml").index
    tree = build_object_tree(index, "Quay", None)
    assert shape(tree.entries) == [
        ("CompositeFrame", 0, False),
        ("SiteFrame", 1, False),
        ("StopPlace", 2, False),
        ("Quay", 3, True),
        ("StopPlace", 2, False),
        ("Quay", 3, True),
        ("StopPlace", 2, False),
        ("Quay", 3, True),
    ]
    assert tree.total == 3
    only = build_object_tree(index, "Quay", "SYN2")
    assert [e.element.xml_id for e in only.entries if e.matches] == ["ch:1:sloid:SYN2:0:1"]
    assert build_object_tree(index, "Quay", "gibt-es-nicht").entries == []


def test_matching_frame_is_header() -> None:
    index = load("ch20_three_stops.xml").index
    tree = build_object_tree(index, "SiteFrame", None)
    assert shape(tree.entries) == [("CompositeFrame", 0, False), ("SiteFrame", 1, True)]


OUTSIDE = b"""<?xml version="1.0" encoding="UTF-8"?>
<PublicationDelivery xmlns="http://www.netex.org.uk/netex" version="2.1">
  <Loose id="a"><wrapper><Inner id="b"/></wrapper></Loose>
  <dataObjects>
    <SiteFrame id="f" version="1">
      <Thing id="c"><Part id="d"/></Thing>
      <frames><ServiceFrame id="g" version="1"/></frames>
    </SiteFrame>
  </dataObjects>
  <Odd id="o"><dataObjects><ResourceFrame id="h" version="1"/></dataObjects></Odd>
</PublicationDelivery>
"""


def test_objects_outside_frames_and_nested_frames() -> None:
    index = open_dataset([SourceFile("o.xml", OUTSIDE)], (), REF_TARGETS).index
    tree = build_object_tree(index, None, None)
    assert shape(tree.outside) == [("Loose", 0, True), ("Inner", 1, True), ("Odd", 0, True)]
    assert shape(tree.entries) == [
        ("SiteFrame", 0, True),
        ("Thing", 1, True),
        ("Part", 2, True),
        ("ServiceFrame", 1, True),
        ("ResourceFrame", 0, True),
    ]
    only = build_object_tree(index, "Inner", None)
    assert shape(only.outside) == [("Loose", 0, False), ("Inner", 1, True)]
    assert only.entries == []


def test_truncation_is_reported() -> None:
    index = load("ch20_three_stops.xml").index
    tree = build_object_tree(index, None, None, limit=4)
    assert tree.shown == 4
    assert tree.total > 4
    assert tree.truncated
    assert len(tree.entries) >= 4
