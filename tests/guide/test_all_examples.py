"""Alle Beispiele des Guide-Klons laden.

Verbindlich laut docs/decisions.md („Alle Guide-Beispiele ladbar“).

Ein Absturz des Tools lässt den Test fehlschlagen. Fehler oder ein veralteter Stand im Beispiel
selbst sind kein Testfehler; sie stehen als Ergebnis in `guide-tested.json`.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from app.core.config import load_config
from app.core.dataset import SourceFile, open_dataset
from app.core.explorer import element_xml_window, object_detail
from app.core.guide.examples import examples_dir, list_examples
from app.core.projection.journeys import LookupStatus, list_journeys
from tests.support import PROJECT_ROOT

GUIDE = load_config(PROJECT_ROOT).settings.guide_path
EXAMPLE_NAMES = [example.name for example in list_examples(GUIDE)]


def test_examples_found(guide_path: Path) -> None:
    assert len(list_examples(guide_path)) >= 22


@pytest.mark.parametrize("name", EXAMPLE_NAMES)
def test_example_loads_without_crash(guide_path: Path, name: str) -> None:
    data = (examples_dir(guide_path) / name).read_bytes()
    dataset = open_dataset(
        [SourceFile(name, data)], load_config(PROJECT_ROOT).not_relevant_elements
    )
    index = dataset.index
    text = index.file_text(1)
    assert text is not None
    total, objects = index.search_objects(None, None, 10_000, 0)
    assert total == len(objects)
    for element in objects:
        assert element.end is not None
        snippet = text[element.start.char : element.end.char]
        assert snippet.startswith("<") and snippet.endswith(">")
    list_journeys(index)
    if objects:
        assert object_detail(index, objects[0].id) is not None
        assert element_xml_window(index, objects[-1].id) is not None
    dataset.close()


def test_example_01_journey(guide_path: Path) -> None:
    name = "01_NeTEx_Spiez_Interlaken_Ost.xml"
    dataset = open_dataset([SourceFile(name, (examples_dir(guide_path) / name).read_bytes())], ())
    [journey] = list_journeys(dataset.index)
    assert [number.text for number in journey.train_numbers] == ["99999"]
    assert journey.line.text == "RE"
    assert journey.departure_time.text == "10:35:00"
    assert (journey.first_stop.status, journey.first_stop.text) == (LookupStatus.FOUND, "Spiez")
    assert journey.last_stop.text == "Interlaken Ost"
