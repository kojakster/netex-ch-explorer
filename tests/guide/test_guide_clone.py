"""Tests gegen den echten Guide-Klon.

Übersprungen, wenn er fehlt; unter `scripts/test.py` Pflicht.
"""

from __future__ import annotations

import re
from pathlib import Path

from app.core.guide.layout import MAPPING_TABLE_FILE
from app.core.guide.mapping import SHEET_SPECS, read_mapping_table
from app.core.guide.status import inspect_guide
from tests.support import REF_TARGETS

SHA = re.compile(r"^[0-9a-f]{40}$")
DATE = re.compile(r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{2}:\d{2}$")


def test_guide_revision_is_read(guide_path: Path, tmp_path: Path) -> None:
    status = inspect_guide(guide_path, tmp_path / "guide-tested.json", REF_TARGETS)
    assert status.found
    assert status.revision.branch == "next"
    assert status.revision.commit is not None
    assert SHA.match(status.revision.commit)
    # Der Klon ist echt: lose oder im Pack ohne Delta, das Datum muss lesbar sein.
    assert status.revision.commit_date is not None
    assert DATE.match(status.revision.commit_date)
    assert status.revision.xsd_commit is not None
    assert SHA.match(status.revision.xsd_commit)
    assert status.xsd_present


def test_mapping_table_is_complete(guide_path: Path) -> None:
    table = read_mapping_table(guide_path.joinpath(*MAPPING_TABLE_FILE.parts))
    assert table.issues == ()
    assert set(table.sheets) == {spec.name for spec in SHEET_SPECS}
    for sheet in table.sheets.values():
        assert sheet.rows, sheet.name
        for row in sheet.rows:
            # Die erste Spalte trägt den Code bzw. Wert der Zeile.
            assert row.values, (sheet.name, row.row)


def test_mapping_table_ends_at_first_empty_row(guide_path: Path) -> None:
    """Danach folgen Bemerkungen (`Angebote`) bzw. eine HRDF-Auswertung (`Weightening`)."""
    table = read_mapping_table(guide_path.joinpath(*MAPPING_TABLE_FILE.parts))
    weighting = table.sheets["Weightening"]
    assert [row.values["NeTEx StopPlace/Weighting"] for row in weighting.rows] == [
        "noInterchange",
        "interchangeAllowed",
        "recommendedInterchange",
        "preferredInterchange",
    ]
    offers = table.sheets["Angebote"]
    assert not any(
        value.startswith("Remarks") for row in offers.rows for value in row.values.values()
    )
