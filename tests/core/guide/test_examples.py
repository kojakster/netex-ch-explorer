from __future__ import annotations

from pathlib import Path

from app.core.dataset import SourceFile, open_dataset
from app.core.guide.examples import (
    Example,
    ExampleResult,
    example_result,
    list_examples,
    read_example,
)
from tests.support import FIXTURES_DIR


def test_list_examples_with_titles(synthetic_guide: Path) -> None:
    examples = list_examples(synthetic_guide)
    assert examples == [
        Example("broken_xml.xml", "Kaputt"),
        Example("ch20_midnight.xml", None),
        Example("ch20_three_stops.xml", "Synthetische Fahrt"),
    ]


def test_list_examples_without_folder(tmp_path: Path) -> None:
    assert list_examples(tmp_path) == []


def test_read_example_only_known_names(synthetic_guide: Path) -> None:
    examples = list_examples(synthetic_guide)
    assert read_example(synthetic_guide, "ch20_three_stops.xml", examples) is not None
    for name in ("../README.md", "README.md", "/etc/passwd", "fehlt.xml"):
        assert read_example(synthetic_guide, name, examples) is None


def test_read_example_rejects_deleted_file(synthetic_guide: Path) -> None:
    examples = list_examples(synthetic_guide)
    (synthetic_guide / "src" / "examples" / "ch20_midnight.xml").unlink()
    assert read_example(synthetic_guide, "ch20_midnight.xml", examples) is None


def result_of(*sources: SourceFile) -> ExampleResult:
    return example_result(open_dataset(sources, ()))


def test_example_results() -> None:
    def fixture(name: str) -> SourceFile:
        return SourceFile(name, (FIXTURES_DIR / name).read_bytes())

    assert result_of(fixture("ch20_three_stops.xml")) is ExampleResult.CLEAN
    assert result_of(fixture("broken_xml.xml")) is ExampleResult.UNREADABLE
    assert result_of() is ExampleResult.UNREADABLE
