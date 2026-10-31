"""Beispiele des Guides (`src/examples/*.xml`): Liste, Titel, Inhalt und Ergebnis.

Titel: In `src/examples/README.md` steht vor jedem Link auf eine Beispieldatei eine Überschrift;
der Titel ist die letzte Überschrift vor dem Link. Mehrere Dateien können denselben Titel haben.
Dateien ohne Link im README haben keinen Titel (angezeigt wird der Dateiname).
"""

from __future__ import annotations

import re
from collections.abc import Iterable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import Final

from app.core.dataset import Dataset
from app.core.guide.layout import EXAMPLES_DIR
from app.core.messages import Severity

EXAMPLES_README: Final = "README.md"
MAX_EXAMPLE_BYTES: Final = 50 * 1024 * 1024
_HEADING = re.compile(r"^#{1,6}\s+(.+?)\s*$")
_LINK = re.compile(r"\]\(([^)\s]+\.xml)\)")


class ExampleResult(StrEnum):
    """Ergebnis eines Beispiels (gespeichert in `guide-tested.json`)."""

    CLEAN = "clean"
    """Ohne Meldungen."""
    NOTES = "notes"
    """Mit Hinweisen oder Warnungen."""
    ERRORS = "errors"
    """Mit Fehlern."""
    UNREADABLE = "unreadable"
    """Nicht lesbar."""
    CHECK_FAILED = "check_failed"
    """Die Prüfung ist fehlgeschlagen (Fehler in der Prüfung, nicht im Beispiel)."""


@dataclass(frozen=True)
class Example:
    """Ein Beispiel: Dateiname und Titel aus dem README (falls vorhanden)."""

    name: str
    title: str | None


def examples_dir(guide_path: Path) -> Path:
    """Ordner der Beispiele im Guide-Klon."""
    return guide_path.joinpath(*EXAMPLES_DIR.parts)


def _titles(readme: Path) -> dict[str, str]:
    if not readme.is_file():
        return {}
    titles: dict[str, str] = {}
    heading: str | None = None
    for line in readme.read_text(encoding="utf-8", errors="replace").splitlines():
        match = _HEADING.match(line)
        if match:
            heading = match.group(1)
            continue
        for link in _LINK.findall(line):
            name = Path(link).name
            if heading is not None and name not in titles:
                titles[name] = heading
    return titles


def list_examples(guide_path: Path) -> list[Example]:
    """Alle XML-Dateien im Beispielordner, nach Namen sortiert."""
    directory = examples_dir(guide_path)
    if not directory.is_dir():
        return []
    titles = _titles(directory / EXAMPLES_README)
    return [
        Example(path.name, titles.get(path.name))
        for path in sorted(directory.glob("*.xml"))
        if path.is_file()
    ]


def example_path(guide_path: Path, name: str, known: Iterable[Example]) -> Path | None:
    """Pfad eines Beispiels; nur Namen aus der Beispielliste, nie freie Pfade."""
    if name not in {example.name for example in known}:
        return None
    path = examples_dir(guide_path) / name
    if not path.is_file() or path.stat().st_size > MAX_EXAMPLE_BYTES:
        return None
    return path


def read_example(guide_path: Path, name: str, known: Iterable[Example]) -> bytes | None:
    """Inhalt eines Beispiels; nur Namen aus der Beispielliste, nie freie Pfade."""
    path = example_path(guide_path, name, known)
    return None if path is None else path.read_bytes()


def example_result(dataset: Dataset) -> ExampleResult:
    """Ergebnis eines geöffneten Beispiels aus seinen Diagnosen."""
    files = dataset.index.files()
    if not files or not all(summary.readable for summary in files):
        return ExampleResult.UNREADABLE
    severities = {item.diagnostic.severity for item in dataset.index.diagnostics()}
    if Severity.ERROR in severities:
        return ExampleResult.ERRORS
    if severities:
        return ExampleResult.NOTES
    return ExampleResult.CLEAN
