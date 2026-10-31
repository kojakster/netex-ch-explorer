"""Die Liste `config/ref-targets.json` gegen XSD und Beispiele des echten Guide-Klons."""

from __future__ import annotations

import json
from pathlib import Path

from app.core.config import load_config
from app.core.dataset import SourceFile, open_dataset
from app.core.guide.layout import EXAMPLES_DIR
from app.core.index.references import ResolveStatus
from tests.support import PROJECT_ROOT


def test_every_entry_is_declared_in_the_xsd(guide_path: Path) -> None:
    """Jeder Eintrag ist mit Elementname und Typ in der XSD des Guide-Stands belegt."""
    config = json.loads((PROJECT_ROOT / "config" / "ref-targets.json").read_text(encoding="utf-8"))
    text = "\n".join(
        path.read_text(encoding="utf-8")
        for path in sorted((guide_path / "xsd" / "xsd").rglob("*.xsd"))
    )
    missing = [
        f"{name}: {entry['xsdType']}"
        for name, entry in config["refs"].items()
        if f'<xsd:element name="{name}" type="{entry["xsdType"]}"' not in text
    ]
    assert missing == [], f"nicht (mehr) in der XSD deklariert: {missing}"


def test_no_example_reference_misses_a_list_entry(guide_path: Path) -> None:
    """Zeigt eine nicht aufgelöste Referenz auf eine ID anderen Typs, fehlt ein Listeneintrag.

    Ein Beispiel ohne Listeneintrag wäre sonst ein falscher Fehler (Entscheid „Zieltyp“); der Test
    nennt den Ref-Namen und den Typ, der in `config/ref-targets.json` zu ergänzen ist.
    """
    ref_targets = load_config(PROJECT_ROOT).ref_targets
    proposals: set[str] = set()
    for path in sorted(guide_path.joinpath(*EXAMPLES_DIR.parts).glob("*.xml")):
        index = open_dataset([SourceFile(path.name, path.read_bytes())], (), ref_targets).index
        root = index.element(1)
        assert root is not None
        elements = index.descendants(root.id, 1_000_000)
        types_by_id: dict[str, set[str]] = {}
        for element in elements:
            if element.xml_id:
                types_by_id.setdefault(element.xml_id, set()).add(element.name)
        for element in elements:
            row = index.reference(element.id)
            if row is None or row.status is ResolveStatus.RESOLVED:
                continue
            other_types = types_by_id.get(row.target_ref, set()) - set(row.expected)
            if other_types:
                proposals.add(f"{element.name} -> {sorted(other_types)} ({path.name})")
    assert sorted(proposals) == [], f"config/ref-targets.json ergänzen: {sorted(proposals)}"
