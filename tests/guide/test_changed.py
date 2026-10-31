from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

from app.core.guide.examples import examples_dir
from tests.guide.changed import CHANGED_HINT, example_changed, expectations

NAME = "ch20_three_stops.xml"


def record(path: Path, guide: Path, sha256: str | None) -> Path:
    examples = {} if sha256 is None else {NAME: {"sha256": sha256, "result": "clean"}}
    path.write_text(
        json.dumps({"schemaVersion": 2, "guide": {"commit": "a" * 40}, "examples": examples}),
        encoding="utf-8",
    )
    return path


def sha_of(guide: Path) -> str:
    return hashlib.sha256((examples_dir(guide) / NAME).read_bytes()).hexdigest()


def test_unchanged_example_keeps_the_plain_failure(synthetic_guide: Path, tmp_path: Path) -> None:
    path = record(tmp_path / "t.json", synthetic_guide, sha_of(synthetic_guide))
    assert not example_changed(synthetic_guide, NAME, path)
    with pytest.raises(AssertionError), expectations(synthetic_guide, NAME, path):
        raise AssertionError


def test_changed_example_reports_the_hint(synthetic_guide: Path, tmp_path: Path) -> None:
    path = record(tmp_path / "t.json", synthetic_guide, "0" * 64)
    assert example_changed(synthetic_guide, NAME, path)
    with (
        pytest.raises(pytest.fail.Exception, match=CHANGED_HINT),
        expectations(synthetic_guide, NAME, path),
    ):
        raise AssertionError


def test_unknown_example_counts_as_changed(synthetic_guide: Path, tmp_path: Path) -> None:
    assert example_changed(synthetic_guide, NAME, tmp_path / "fehlt.json")
    path = record(tmp_path / "t.json", synthetic_guide, None)
    assert example_changed(synthetic_guide, NAME, path)


def test_passing_expectations_are_untouched(synthetic_guide: Path, tmp_path: Path) -> None:
    path = record(tmp_path / "t.json", synthetic_guide, "0" * 64)
    reached = False
    with expectations(synthetic_guide, NAME, path):
        reached = True
    assert reached
