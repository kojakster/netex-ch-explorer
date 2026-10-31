from __future__ import annotations

from app.core.guide.mapping import MappingTable
from app.core.projection.master_data import MasterStatus, lookup_master
from tests.core.projection.builders import TABLE, sheet


def test_found_with_sheet_row_and_texts() -> None:
    info = lookup_master(TABLE, "Angebote", "Facility Value", "bistro")
    assert info.status is MasterStatus.FOUND
    [match] = info.matches
    assert (match.sheet, match.row) == ("Angebote", 4)
    assert match.texts == (("Angebotabkürzung", "WS"), ("Angebottext", "Bistro"))


def test_all_matching_rows_are_returned() -> None:
    info = lookup_master(TABLE, "Angebote", "Facility Value", "doppelt")
    assert [(m.row, dict(m.texts)["Angebotabkürzung"]) for m in info.matches] == [
        (5, "X1"),
        (6, "X2"),
    ]


def test_code_is_compared_exactly_but_without_surrounding_blanks() -> None:
    padded = MappingTable(sheets={"S": sheet("S", [{"Value": "regionalRail ", "Text": "t"}])})
    assert lookup_master(padded, "S", "Value", "regionalRail").status is MasterStatus.FOUND
    assert lookup_master(padded, "S", "Value", " regionalRail  ").status is MasterStatus.FOUND
    assert lookup_master(padded, "S", "Value", "RegionalRail").status is MasterStatus.NONE


def test_unknown_code_has_no_explanation() -> None:
    info = lookup_master(TABLE, "Angebote", "Facility Value", "unbekannt")
    assert info.status is MasterStatus.NONE
    assert info.matches == ()


def test_missing_sheet_or_column_is_unavailable() -> None:
    assert lookup_master(TABLE, "Fehlt", "Value", "x").status is MasterStatus.UNAVAILABLE
    assert lookup_master(TABLE, "StopUse", "Fehlt", "x").status is MasterStatus.UNAVAILABLE
    assert lookup_master(MappingTable(), "StopUse", "Value", "x").status is MasterStatus.UNAVAILABLE
