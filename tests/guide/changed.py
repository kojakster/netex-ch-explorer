"""Fachliche Tests an Guide-Beispielen: ändert sich das Beispiel, weist der Bericht darauf hin.

Verbindlich laut UMSETZUNGSPLAN Abschnitt 11: Hat sich die Prüfsumme des Beispiels seit dem letzten
Testlauf geändert und schlägt die Erwartung fehl, lautet die Meldung „Beispiel geändert,
Erwartung prüfen“ statt nur „fehlgeschlagen“. Die Ursache (Guide oder Tool) wird dann dem Benutzer
vorgelegt.
"""

from __future__ import annotations

import hashlib
from collections.abc import Iterator
from contextlib import contextmanager
from pathlib import Path

import pytest

from app.core.guide.examples import examples_dir
from app.core.guide.guide_tested import TEST_RECORD_FILE, read_test_record
from tests.support import PROJECT_ROOT

CHANGED_HINT = "Beispiel geändert \u2013 Erwartung prüfen"


def example_changed(
    guide_path: Path, name: str, record_path: Path = PROJECT_ROOT / TEST_RECORD_FILE
) -> bool:
    """Ob die Prüfsumme des Beispiels von der im Testnachweis abweicht (oder keine bekannt ist)."""
    record = read_test_record(record_path)
    known = None if record is None else record.examples.get(name)
    current = hashlib.sha256((examples_dir(guide_path) / name).read_bytes()).hexdigest()
    return known is None or known.sha256 != current


@contextmanager
def expectations(
    guide_path: Path, name: str, record_path: Path = PROJECT_ROOT / TEST_RECORD_FILE
) -> Iterator[None]:
    """Übersetzt eine fehlgeschlagene Erwartung bei geändertem Beispiel in den Hinweis."""
    try:
        yield
    except AssertionError as error:
        if example_changed(guide_path, name, record_path):
            pytest.fail(f"{CHANGED_HINT}: {name}\n{error}", pytrace=False)
        raise
