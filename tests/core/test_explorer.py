from __future__ import annotations

import pytest

from app.core import explorer
from app.core.dataset import Dataset, SourceFile, open_dataset
from app.core.explorer import (
    element_path,
    element_xml_window,
    object_detail,
    position_xml_window,
    xml_window,
)
from tests.support import FIXTURES_DIR


def load(name: str) -> Dataset:
    return open_dataset([SourceFile(name, (FIXTURES_DIR / name).read_bytes())], ())


def test_path_with_positions_only_for_repeated_names() -> None:
    index = load("ch20_three_stops.xml").index
    [quay] = index.objects_by_id("ch:1:sloid:SYN2:0:1", "Quay")
    assert element_path(index, quay) == (
        "/PublicationDelivery/dataObjects/CompositeFrame/frames/SiteFrame/stopPlaces"
        "/StopPlace[2]/quays/Quay"
    )


def test_object_detail_tree() -> None:
    index = load("ch20_three_stops.xml").index
    [stop] = index.objects_by_id("ch:1:sloid:SYN1", "StopPlace")
    detail = object_detail(index, stop.id)
    assert detail is not None
    assert detail.frame is not None
    assert detail.frame.name == "SiteFrame"
    assert [node.element.name for node in detail.properties] == ["Name", "quays"]
    quays = detail.properties[1]
    assert [node.element.name for node in quays.children] == ["Quay"]
    assert [node.element.name for node in quays.children[0].children] == ["PublicCode"]
    assert not detail.truncated
    assert object_detail(index, 99999) is None


def test_object_detail_is_truncated(monkeypatch: pytest.MonkeyPatch) -> None:
    index = load("ch20_three_stops.xml").index
    monkeypatch.setattr(explorer, "MAX_PROPERTY_NODES", 2)
    root = index.element(1)
    assert root is not None
    detail = object_detail(index, root.id)
    assert detail is not None
    assert detail.truncated
    assert [node.element.name for node in detail.properties] == [
        "PublicationTimestamp",
        "ParticipantRef",
    ]


def test_element_window_marks_exact_range() -> None:
    index = load("ch20_three_stops.xml").index
    [quay] = index.objects_by_id("ch:1:sloid:SYN2:0:1", "Quay")
    window = element_xml_window(index, quay.id)
    assert window is not None
    marked = window.text[window.focus_from : window.focus_to]
    assert marked.startswith('<Quay id="ch:1:sloid:SYN2:0:1"')
    assert marked.endswith("</Quay>")
    assert window.first_line == quay.start.line - explorer.CONTEXT_LINES
    assert window.file_name == "ch20_three_stops.xml"
    assert [band.frame.name for band in window.frames] == [
        "CompositeFrame",
        "ResourceFrame",
        "SiteFrame",
        "ServiceFrame",
    ]
    site = window.frames[2]
    assert site.from_line <= quay.start.line <= site.to_line
    assert element_xml_window(index, 99999) is None


def test_window_at_file_start_and_truncation(monkeypatch: pytest.MonkeyPatch) -> None:
    index = load("ch20_three_stops.xml").index
    root = index.element(1)
    assert root is not None
    monkeypatch.setattr(explorer, "MAX_WINDOW_LINES", 10)
    window = element_xml_window(index, root.id)
    assert window is not None
    assert window.first_line == 1
    assert window.truncated
    assert window.text.count("\n") == 9
    assert window.focus_to == len(window.text)


def test_window_for_unclosed_element_marks_start() -> None:
    index = load("broken_xml.xml").index
    root = index.element(1)
    assert root is not None
    window = element_xml_window(index, root.id)
    assert window is not None
    assert window.focus_from == window.focus_to
    assert window.frames[0].to_line == window.first_line + window.text.count("\n")


def test_position_window() -> None:
    index = load("broken_xml.xml").index
    window = position_xml_window(index, 1, 48, 34)
    assert window is not None
    assert window.text[window.focus_from : window.focus_to] == "N"
    clamped = position_xml_window(index, 1, 10_000, 10_000)
    assert clamped is not None
    assert clamped.focus_from <= len(clamped.text)
    assert position_xml_window(index, 5, 1, 1) is None
    assert xml_window(index, 5, (0, 1), (1, 1)) is None
