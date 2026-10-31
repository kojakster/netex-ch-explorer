"""Mappingtabelle des Guides (`Mappingtabellen_NeTEx_v2.0.xlsx`) lesen.

Regeln (docs/decisions.md, „Mappingtabelle auslesen“):

- Pro Blatt nennt `SheetSpec` die benötigten Spalten über ihre Namen. Die Kopfzeile ist die
  erste Zeile unter den obersten `HEADER_SEARCH_ROWS`, die den Namen der ersten Spalte enthält.
- Spaltennamen werden nur im Leerraum vereinheitlicht (Zeilenumbrüche, doppelte Leerzeichen).
- Die Tabelle endet an der ersten leeren Zeile nach der Kopfzeile; was danach folgt
  (Bemerkungen, Auswertungen), gehört nicht dazu.
- Zellwerte bleiben unverändert (auch Tippfehler und Leerzeichen). Zellfarben werden ignoriert.
- Fehlt ein Blatt, die Kopfzeile oder eine Spalte, entsteht eine Meldung; nichts wird geraten.
- XML im Excel-Paket liest openpyxl mit `defusedxml` (Laufzeitabhängigkeit): keine DTD, keine
  Entitäten.
"""

from __future__ import annotations

import datetime as dt
import zipfile
from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

from openpyxl import load_workbook
from openpyxl.utils.exceptions import InvalidFileException

from app.core.messages import Issue, MessageKey, Severity

HEADER_SEARCH_ROWS: Final = 10
_READ_ERRORS: Final = (
    OSError,
    zipfile.BadZipFile,
    InvalidFileException,
    KeyError,
    ValueError,
    SyntaxError,
)


@dataclass(frozen=True)
class SheetSpec:
    """Benötigte Spalten eines Blatts; die erste Spalte kennzeichnet die Kopfzeile."""

    name: str
    columns: tuple[str, ...]


SHEET_SPECS: Final = (
    SheetSpec(
        "VMArt->NeTEx",
        (
            "Abk",
            "Bezeichnung",
            "Verkehrsträger",
            "Verkehrsmittelkategorie",
            "TransportMode",
            "TransportSubmode",
            "ProductCategory",
            "Remark",
        ),
    ),
    SheetSpec(
        "Angebote",
        (
            "Angebotabkürzung",
            "Angebottext",
            "Klassifizierung in NeTEx",
            "Facility",
            "Facility Value",
            "NoticeType",
            "NoticeContent",
            "Remarks",
        ),
    ),
    SheetSpec(
        "Facilities_gemappt",
        (
            "Facility",
            "Verwendet in HRDF Mapping",
            "Dargestellt in RV 2.0",
            "XSD-Group",
            "Bemerkung / NeTEx 2.0 Hinweis",
        ),
    ),
    SheetSpec("StopPlaceType", ("Value", "Usage", "Description")),
    SheetSpec("QuayType", ("Value", "Usage", "Description")),
    SheetSpec("StopUse", ("Value", "Usage", "Description")),
    SheetSpec(
        "LineType",
        (
            "Value for LineType",
            "Usage in Switzerland",
            # Schreibweise „Siwtzerland“ wie in der Mappingtabelle.
            "NeTEx RG 2.0 - Siwtzerland Status",
            "Recommended TransportSubmode",
            "Remarks (NeTEx 2.1 / Schweizer RV 2.0)",
        ),
    ),
    SheetSpec(
        "Weightening",
        ("NeTEx StopPlace/Weighting", "HRDF HafasPriority BFPRIOS", "HRDF HafasKMInfo"),
    ),
)


@dataclass(frozen=True)
class MappingRow:
    """Eine Datenzeile: Excel-Zeilennummer und nicht leere Werte je Spaltenname."""

    row: int
    values: dict[str, str]


@dataclass(frozen=True)
class MappingSheet:
    """Gelesene Zeilen eines Blatts mit der Zeilennummer der Kopfzeile."""

    name: str
    header_row: int
    rows: tuple[MappingRow, ...]


@dataclass(frozen=True)
class MappingTable:
    """Alle gelesenen Blätter und die Meldungen beim Lesen."""

    sheets: dict[str, MappingSheet] = field(default_factory=dict)
    issues: tuple[Issue, ...] = ()


# openpyxl liefert je nach Zelle Text, Zahl, Wahrheitswert, Datum, Rich Text oder Formel.
type CellValue = object


def read_mapping_table(path: Path, specs: Iterable[SheetSpec] = SHEET_SPECS) -> MappingTable:
    """Liest die benötigten Blätter der Mappingtabelle.

    Die Datei wird nur gelesen und immer geschlossen. Ist sie nicht lesbar, enthält das
    Ergebnis keine Blätter und eine Meldung.
    """
    file_label = path.name
    if not path.is_file():
        return MappingTable(issues=(_issue(MessageKey.MAPPING_FILE_MISSING, file=file_label),))
    try:
        workbook = load_workbook(path, read_only=True, data_only=True)
    except _READ_ERRORS:
        return MappingTable(issues=(_issue(MessageKey.MAPPING_FILE_UNREADABLE, file=file_label),))
    sheets: dict[str, MappingSheet] = {}
    issues: list[Issue] = []
    try:
        for spec in specs:
            if spec.name not in workbook.sheetnames:
                issues.append(_issue(MessageKey.MAPPING_SHEET_MISSING, sheet=spec.name))
                continue
            rows = workbook[spec.name].iter_rows(values_only=True)
            sheet, sheet_issues = _read_sheet(spec, rows)
            issues.extend(sheet_issues)
            if sheet is not None:
                sheets[spec.name] = sheet
    # Im Modus read_only liest openpyxl die Blätter erst hier. SyntaxError umfasst
    # ElementTree.ParseError, ValueError die Abweisungen von defusedxml (DTD, Entitäten).
    except _READ_ERRORS:
        return MappingTable(issues=(_issue(MessageKey.MAPPING_FILE_UNREADABLE, file=file_label),))
    finally:
        workbook.close()
    return MappingTable(sheets=sheets, issues=tuple(issues))


def _read_sheet(
    spec: SheetSpec, rows: Iterator[tuple[CellValue, ...]]
) -> tuple[MappingSheet | None, list[Issue]]:
    marker = spec.columns[0]
    header_row = 0
    header: tuple[str, ...] = ()
    for number, cells in enumerate(rows, start=1):
        if number > HEADER_SEARCH_ROWS:
            break
        names = tuple(_normalize_header(cell) for cell in cells)
        if marker in names:
            header_row, header = number, names
            break
    if not header_row:
        return None, [_issue(MessageKey.MAPPING_HEADER_NOT_FOUND, sheet=spec.name, column=marker)]
    issues: list[Issue] = []
    column_index: dict[str, int] = {}
    for column in spec.columns:
        if column in header:
            column_index[column] = header.index(column)
        else:
            issues.append(_issue(MessageKey.MAPPING_COLUMN_MISSING, sheet=spec.name, column=column))
    data_rows = tuple(_read_data_rows(rows, header_row, column_index))
    return MappingSheet(name=spec.name, header_row=header_row, rows=data_rows), issues


def _read_data_rows(
    rows: Iterator[tuple[CellValue, ...]], header_row: int, column_index: dict[str, int]
) -> Iterator[MappingRow]:
    for number, cells in enumerate(rows, start=header_row + 1):
        texts = [_cell_text(cell) for cell in cells]
        if not any(text.strip() for text in texts):
            return
        values = {
            column: texts[index]
            for column, index in column_index.items()
            if index < len(texts) and texts[index].strip()
        }
        if values:
            yield MappingRow(row=number, values=values)


def _normalize_header(cell: CellValue) -> str:
    return " ".join(_cell_text(cell).split())


def _cell_text(cell: CellValue) -> str:
    """Zellwert als Text, ohne Inhalt zu verändern (Rich Text ergibt seinen reinen Text)."""
    if cell is None:
        return ""
    if isinstance(cell, bool):
        return "TRUE" if cell else "FALSE"
    if isinstance(cell, dt.datetime | dt.date | dt.time):
        return cell.isoformat()
    return str(cell)


def _issue(key: MessageKey, **params: str) -> Issue:
    return Issue(Severity.ERROR, key, dict(params))
