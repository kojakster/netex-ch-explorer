"""Testnachweis `guide-tested.json`: mit welchem Guide-Stand die Tests zuletzt erfolgreich liefen.

Die Datei schreibt nur ein vollständig erfolgreicher Testlauf (`scripts/test.py`). Sie enthält
den Guide- und XSD-Commit und pro Beispiel Prüfsumme (SHA-256) und Ergebnis.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

from app.core.guide.examples import ExampleResult
from app.core.guide.git import is_commit_id

TEST_RECORD_FILE: Final = "guide-tested.json"
TEST_COMMAND: Final = "uv run python scripts/test.py"
SCHEMA_VERSION: Final = 2

_SHA256 = re.compile(r"^[0-9a-f]{64}$")

_MAX_RECORD_BYTES: Final = 5_000_000


class GuideTestRecordError(Exception):
    """Der Testnachweis ist nicht lesbar oder hat nicht das erwartete Format."""


@dataclass(frozen=True)
class ExampleRecord:
    """Prüfsumme und Ergebnis eines Beispiels beim letzten erfolgreichen Testlauf."""

    sha256: str
    result: ExampleResult


@dataclass(frozen=True)
class GuideTestRecord:
    """Guide-Stand des letzten erfolgreichen Testlaufs."""

    guide_commit: str
    xsd_commit: str | None
    examples: dict[str, ExampleRecord] = field(default_factory=dict)


def read_test_record(path: Path) -> GuideTestRecord | None:
    """Liest den Testnachweis; `None`, wenn die Datei fehlt.

    Raises:
        GuideTestRecordError: Die Datei ist nicht lesbar oder ungültig.
    """
    if not path.is_file():
        return None
    try:
        if path.stat().st_size > _MAX_RECORD_BYTES:
            raise GuideTestRecordError(path)
        data: object = json.loads(path.read_text(encoding="utf-8"))
    # RecursionError: sehr tief verschachteltes JSON.
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, RecursionError) as error:
        raise GuideTestRecordError(path) from error
    if not isinstance(data, dict) or data.get("schemaVersion") != SCHEMA_VERSION:
        raise GuideTestRecordError(path)
    guide = data.get("guide")
    if not isinstance(guide, dict):
        raise GuideTestRecordError(path)
    guide_commit = guide.get("commit")
    xsd_commit = guide.get("xsdCommit")
    if not isinstance(guide_commit, str) or not is_commit_id(guide_commit):
        raise GuideTestRecordError(path)
    if xsd_commit is not None and (not isinstance(xsd_commit, str) or not is_commit_id(xsd_commit)):
        raise GuideTestRecordError(path)
    return GuideTestRecord(guide_commit, xsd_commit, _read_examples(data.get("examples"), path))


def _read_examples(raw: object, path: Path) -> dict[str, ExampleRecord]:
    if not isinstance(raw, dict):
        raise GuideTestRecordError(path)
    examples: dict[str, ExampleRecord] = {}
    for name, entry in raw.items():
        if not isinstance(entry, dict):
            raise GuideTestRecordError(path)
        sha256 = entry.get("sha256")
        result = entry.get("result")
        valid_result = isinstance(result, str) and result in set(ExampleResult)
        if not isinstance(sha256, str) or not _SHA256.match(sha256) or not valid_result:
            raise GuideTestRecordError(path)
        examples[str(name)] = ExampleRecord(sha256, ExampleResult(str(result)))
    return examples


def write_test_record(path: Path, record: GuideTestRecord) -> None:
    """Schreibt den Testnachweis (UTF-8, stabile Reihenfolge, abschliessender Zeilenumbruch)."""
    data = {
        "schemaVersion": SCHEMA_VERSION,
        "guide": {"commit": record.guide_commit, "xsdCommit": record.xsd_commit},
        "examples": {
            name: {"sha256": example.sha256, "result": example.result}
            for name, example in sorted(record.examples.items())
        },
    }
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
