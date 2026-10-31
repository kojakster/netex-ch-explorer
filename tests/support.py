"""Konstanten für die Tests."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

from app.core.config import load_config
from app.core.index.dataset_index import DatasetIndex, ElementRow

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = PROJECT_ROOT / "fixtures"
LOCALES_DIR = PROJECT_ROOT / "app" / "frontend" / "src" / "locales"
REQUIRE_GUIDE_ENV = "NETEX_REQUIRE_GUIDE"
# Die Zieltyp-Liste der Anwendung (config/ref-targets.json): Tests prüfen so das echte Verhalten.
REF_TARGETS = load_config(PROJECT_ROOT).ref_targets

SHA_A = "a" * 40
SHA_B = "b" * 40

type GitRepoFactory = Callable[..., Path]
type WorkbookFactory = Callable[[Path, Mapping[str, Sequence[Sequence[object]]]], Path]


def objects_by_id(index: DatasetIndex, xml_id: str, object_type: str) -> list[ElementRow]:
    """Objekte mit dieser `id` und diesem Typ (Elementname), in Dokumentreihenfolge."""
    return [row for row in index.elements_by_name([object_type]) if row.xml_id == xml_id]
