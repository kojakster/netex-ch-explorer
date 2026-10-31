from __future__ import annotations

import datetime as dt
import zipfile
from collections.abc import Callable
from pathlib import Path

from openpyxl import xml as openpyxl_xml

from app.core.guide.mapping import (
    HEADER_SEARCH_ROWS,
    SheetSpec,
    read_mapping_table,
)
from app.core.messages import MessageKey, Severity
from tests.support import WorkbookFactory

SPEC = (SheetSpec("StopUse", ("Value", "Usage", "Description")),)


def test_reads_rows_until_first_empty_row(tmp_path: Path, make_workbook: WorkbookFactory) -> None:
    path = make_workbook(
        tmp_path / "m.xlsx",
        {
            "StopUse": [
                ["StopUse"],
                ["StopUse in ServiceJourneyPattern"],
                ["Value", "Usage", "Description"],
                ["access", "Default", "Regular value"],
                ["passthrough ", "Later"],
                [None, None, None],
                ["Remarks:", "nicht Teil der Tabelle"],
            ]
        },
    )
    table = read_mapping_table(path, SPEC)
    assert table.issues == ()
    sheet = table.sheets["StopUse"]
    assert sheet.header_row == 3
    assert [(row.row, row.values) for row in sheet.rows] == [
        (4, {"Value": "access", "Usage": "Default", "Description": "Regular value"}),
        # Werte bleiben unverändert, auch mit Leerzeichen am Ende.
        (5, {"Value": "passthrough ", "Usage": "Later"}),
    ]


def test_header_names_are_whitespace_normalized(
    tmp_path: Path, make_workbook: WorkbookFactory
) -> None:
    spec = (SheetSpec("LineType", ("Value for LineType", "Usage in Switzerland")),)
    path = make_workbook(
        tmp_path / "m.xlsx",
        {"LineType": [["Value for LineType", "Usage in\nSwitzerland  "], ["local", "n/a"]]},
    )
    table = read_mapping_table(path, spec)
    assert table.issues == ()
    assert table.sheets["LineType"].rows[0].values == {
        "Value for LineType": "local",
        "Usage in Switzerland": "n/a",
    }


def test_cell_types_become_text(tmp_path: Path, make_workbook: WorkbookFactory) -> None:
    spec = (SheetSpec("S", ("Code", "A", "B", "C")),)
    path = make_workbook(
        tmp_path / "m.xlsx",
        {"S": [["Code", "A", "B", "C"], [115, True, 0.5, dt.datetime(2026, 1, 2, 3, 4, 5)]]},
    )
    values = read_mapping_table(path, spec).sheets["S"].rows[0].values
    assert values == {"Code": "115", "A": "TRUE", "B": "0.5", "C": "2026-01-02T03:04:05"}


def test_rows_without_configured_values_are_skipped(
    tmp_path: Path, make_workbook: WorkbookFactory
) -> None:
    spec = (SheetSpec("S", ("Code",)),)
    path = make_workbook(
        tmp_path / "m.xlsx", {"S": [["Code", "Andere"], [None, "nur andere Spalte"], ["x"]]}
    )
    rows = read_mapping_table(path, spec).sheets["S"].rows
    assert [(row.row, row.values) for row in rows] == [(3, {"Code": "x"})]


def test_missing_column_is_reported(tmp_path: Path, make_workbook: WorkbookFactory) -> None:
    path = make_workbook(
        tmp_path / "m.xlsx", {"StopUse": [["Value", "Usage"], ["access", "Default"]]}
    )
    table = read_mapping_table(path, SPEC)
    assert [(i.key, i.params) for i in table.issues] == [
        (MessageKey.MAPPING_COLUMN_MISSING, {"sheet": "StopUse", "column": "Description"})
    ]
    assert table.issues[0].severity is Severity.ERROR
    assert table.sheets["StopUse"].rows[0].values == {"Value": "access", "Usage": "Default"}


def test_missing_header_is_reported(tmp_path: Path, make_workbook: WorkbookFactory) -> None:
    rows: list[list[object]] = [["Titel"]] * (HEADER_SEARCH_ROWS + 1)
    path = make_workbook(tmp_path / "m.xlsx", {"StopUse": [*rows, ["Value"]]})
    table = read_mapping_table(path, SPEC)
    assert "StopUse" not in table.sheets
    assert [i.key for i in table.issues] == [MessageKey.MAPPING_HEADER_NOT_FOUND]


def test_missing_sheet_is_reported(tmp_path: Path, make_workbook: WorkbookFactory) -> None:
    path = make_workbook(tmp_path / "m.xlsx", {"Andere": [["x"]]})
    table = read_mapping_table(path, SPEC)
    assert table.sheets == {}
    assert [(i.key, i.params) for i in table.issues] == [
        (MessageKey.MAPPING_SHEET_MISSING, {"sheet": "StopUse"})
    ]


def test_missing_file(tmp_path: Path) -> None:
    table = read_mapping_table(tmp_path / "fehlt.xlsx", SPEC)
    assert [i.key for i in table.issues] == [MessageKey.MAPPING_FILE_MISSING]


def test_unreadable_file(tmp_path: Path) -> None:
    path = tmp_path / "kaputt.xlsx"
    path.write_bytes(b"kein zip")
    table = read_mapping_table(path, SPEC)
    assert [(i.key, i.params) for i in table.issues] == [
        (MessageKey.MAPPING_FILE_UNREADABLE, {"file": "kaputt.xlsx"})
    ]


def rewrite_sheet_xml(path: Path, change: Callable[[str], str]) -> None:
    """Ändert das XML des ersten Blatts im Excel-Paket (für Fehler- und Sicherheitstests)."""
    with zipfile.ZipFile(path) as source:
        entries = {info.filename: source.read(info) for info in source.infolist()}
    sheet = "xl/worksheets/sheet1.xml"
    entries[sheet] = change(entries[sheet].decode("utf-8")).encode("utf-8")
    with zipfile.ZipFile(path, "w") as target:
        for name, data in entries.items():
            target.writestr(name, data)


def test_broken_sheet_xml_is_reported(tmp_path: Path, make_workbook: WorkbookFactory) -> None:
    path = make_workbook(tmp_path / "m.xlsx", {"StopUse": [["Value"], ["access"]]})
    rewrite_sheet_xml(path, lambda xml: xml[: len(xml) // 2])
    table = read_mapping_table(path, SPEC)
    assert table.sheets == {}
    assert [i.key for i in table.issues] == [MessageKey.MAPPING_FILE_UNREADABLE]


def test_entities_in_sheet_xml_are_rejected(tmp_path: Path, make_workbook: WorkbookFactory) -> None:
    """XXE-Schutz: openpyxl liest mit defusedxml; DTD und Entitäten führen zu einer Meldung."""
    secret = tmp_path / "secret.txt"
    secret.write_text("XXE-GEHEIMNIS", encoding="utf-8")
    path = make_workbook(tmp_path / "m.xlsx", {"StopUse": [["Value"], ["access"]]})

    def add_entity(xml: str) -> str:
        declaration, _, rest = xml.partition("?>")
        doctype = f'<!DOCTYPE worksheet [<!ENTITY x SYSTEM "{secret.as_uri()}">]>'
        return declaration + "?>" + doctype + rest.replace(">access<", ">&x;<", 1)

    rewrite_sheet_xml(path, add_entity)
    table = read_mapping_table(path, SPEC)
    assert [i.key for i in table.issues] == [MessageKey.MAPPING_FILE_UNREADABLE]
    assert "XXE-GEHEIMNIS" not in repr(table)


def test_openpyxl_uses_defusedxml() -> None:
    assert openpyxl_xml.DEFUSEDXML
