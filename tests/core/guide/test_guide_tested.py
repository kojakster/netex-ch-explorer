from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.core.guide.examples import ExampleResult
from app.core.guide.guide_tested import (
    ExampleRecord,
    GuideTestRecord,
    GuideTestRecordError,
    read_test_record,
    write_test_record,
)
from tests.support import SHA_A, SHA_B


def test_round_trip(tmp_path: Path) -> None:
    path = tmp_path / "guide-tested.json"
    record = GuideTestRecord(
        guide_commit=SHA_A,
        xsd_commit=SHA_B,
        examples={"01.xml": ExampleRecord("c" * 64, ExampleResult.NOTES)},
    )
    write_test_record(path, record)
    assert read_test_record(path) == record
    assert path.read_text(encoding="utf-8").endswith("}\n")


def test_without_xsd_commit(tmp_path: Path) -> None:
    path = tmp_path / "guide-tested.json"
    write_test_record(path, GuideTestRecord(guide_commit=SHA_A, xsd_commit=None))
    assert read_test_record(path) == GuideTestRecord(guide_commit=SHA_A, xsd_commit=None)


def test_missing_file(tmp_path: Path) -> None:
    assert read_test_record(tmp_path / "fehlt.json") is None


@pytest.mark.parametrize(
    "content",
    [
        "{kaputt",
        "[" * 200_000,
        json.dumps([]),
        json.dumps({"schemaVersion": 1, "guide": {"commit": SHA_A}}),
        json.dumps({"schemaVersion": 2}),
        json.dumps({"schemaVersion": 2, "guide": {"commit": "abc"}, "examples": {}}),
        json.dumps(
            {"schemaVersion": 2, "guide": {"commit": SHA_A, "xsdCommit": 5}, "examples": {}}
        ),
        json.dumps({"schemaVersion": 2, "guide": {"commit": SHA_A}}),
        json.dumps({"schemaVersion": 2, "guide": {"commit": SHA_A}, "examples": {"a": 1}}),
        json.dumps(
            {
                "schemaVersion": 2,
                "guide": {"commit": SHA_A},
                "examples": {"a": {"sha256": "x", "result": "clean"}},
            }
        ),
        json.dumps(
            {
                "schemaVersion": 2,
                "guide": {"commit": SHA_A},
                "examples": {"a": {"sha256": "c" * 64, "result": "gut"}},
            }
        ),
    ],
)
def test_invalid_content(tmp_path: Path, content: str) -> None:
    path = tmp_path / "guide-tested.json"
    path.write_text(content, encoding="utf-8")
    with pytest.raises(GuideTestRecordError):
        read_test_record(path)


def test_too_large(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    path = tmp_path / "guide-tested.json"
    write_test_record(path, GuideTestRecord(guide_commit=SHA_A, xsd_commit=None))
    monkeypatch.setattr("app.core.guide.guide_tested._MAX_RECORD_BYTES", 10)
    with pytest.raises(GuideTestRecordError):
        read_test_record(path)
