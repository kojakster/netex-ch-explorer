"""Datensatz: eine oder mehrere eingelesene Dateien mit gemeinsamem Index."""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass

from app.core.index.dataset_index import DatasetIndex
from app.core.reader.xml_reader import read_xml


@dataclass(frozen=True)
class SourceFile:
    """Eine Datei zum Öffnen: Anzeigename und Inhalt."""

    name: str
    data: bytes


class Dataset:
    """Geöffneter Datensatz; schliessen gibt den Index frei."""

    def __init__(self, index: DatasetIndex) -> None:
        self.index = index

    def close(self) -> None:
        """Gibt den Index frei."""
        self.index.close()


def open_dataset(sources: Iterable[SourceFile], not_relevant: Iterable[str]) -> Dataset:
    """Liest alle Dateien ein und baut den Index. Fehler werden zu Diagnosen."""
    parsed = [read_xml(source.name, source.data) for source in sources]
    return Dataset(DatasetIndex(parsed, not_relevant))
