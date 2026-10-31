"""Bedeutung von Codes aus den Stammdaten (Mappingtabelle des Guides).

Regeln (docs/decisions.md, „Anzeige von Codes und Stammdaten“): Der gesendete Code wird immer
gezeigt. Eine Bedeutung kommt nur aus der Datei selbst oder aus der Mappingtabelle, mit Blatt und
Zeile; sonst steht da „keine Erläuterung in den Stammdaten“. Verglichen wird der Code exakt (mit
Gross-/Kleinschreibung), nur umgebender Leerraum bleibt unberücksichtigt, weil die Tabelle ihn
enthält (z. B. `regionalRail␣`). Passen mehrere Zeilen, werden alle gezeigt.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.core.guide.mapping import MappingTable


class MasterStatus(StrEnum):
    """Ergebnis einer Suche in den Stammdaten."""

    FOUND = "found"
    NONE = "none"
    """Die Tabelle ist lesbar, enthält den Code aber nicht."""
    UNAVAILABLE = "unavailable"
    """Das Blatt oder die Code-Spalte fehlt in der Mappingtabelle."""


@dataclass(frozen=True)
class MasterMatch:
    """Eine passende Zeile: Blatt, Excel-Zeilennummer und die Werte der übrigen Spalten."""

    sheet: str
    row: int
    texts: tuple[tuple[str, str], ...]


@dataclass(frozen=True)
class MasterInfo:
    """Bedeutung eines Codes aus den Stammdaten."""

    status: MasterStatus
    matches: tuple[MasterMatch, ...] = ()


def lookup_master(table: MappingTable, sheet: str, key_column: str, code: str) -> MasterInfo:
    """Sucht `code` in der Spalte `key_column` des Blatts `sheet`."""
    found = table.sheets.get(sheet)
    if found is None or not any(key_column in row.values for row in found.rows):
        return MasterInfo(MasterStatus.UNAVAILABLE)
    wanted = code.strip()
    matches = tuple(
        MasterMatch(
            sheet,
            row.row,
            tuple((column, value) for column, value in row.values.items() if column != key_column),
        )
        for row in found.rows
        if row.values.get(key_column, "").strip() == wanted
    )
    return MasterInfo(MasterStatus.FOUND if matches else MasterStatus.NONE, matches)
