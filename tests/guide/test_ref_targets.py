"""Die Liste `config/ref-targets.json` gegen XSD und Beispiele des echten Guide-Klons."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from app.core.dataset import SourceFile, open_dataset
from app.core.guide.layout import EXAMPLES_DIR, TEMPLATES_DIR
from app.core.index.references import ResolveStatus
from app.core.reader.xml_reader import read_xml
from tests.guide.xsd_refs import load_xsd_refs
from tests.support import PROJECT_ROOT, REF_TARGETS

# Ab dieser Zahl erlaubter Klassen gilt der Ref-Typ als unbeschränkt (XSD: jede Klasse, 3765).
UNRESTRICTED_LIMIT = 1000
# Unbeschränkte Ref-Namen der Guide-Dateien: Die Liste nennt den praktischen Zieltyp von Hand.
UNRESTRICTED = frozenset(
    {
        "EndPointInPatternRef",
        "FromPointInPatternRef",
        "StartPointInPatternRef",
        "ToPointInPatternRef",
    }
)
# Zieltypen, die ein Guide-Beispiel verwendet, die die XSD aber nicht nennt (offener Punkt 5).
EXTRA_BEYOND_XSD = {"ParentJourneyRef": frozenset({"ServiceJourney"})}
# Ref-Namen in Guide-Vorlagen, die die XSD nicht deklariert (Fehler der Vorlagen, nicht erfunden).
GUIDE_WITHOUT_XSD = frozenset({"FromProductCategoryRef", "ToProductCategoryRef"})


def _listed_refs() -> dict[str, dict[str, Any]]:
    config = json.loads((PROJECT_ROOT / "config" / "ref-targets.json").read_text(encoding="utf-8"))
    refs: dict[str, dict[str, Any]] = config["refs"]
    return refs


def _guide_ref_names(guide_path: Path) -> dict[str, set[str]]:
    """Ref-Namen (ohne `nameOfRefClass`) in Beispielen und Vorlagen des Guides, mit Dateien."""
    names: dict[str, set[str]] = {}
    for directory in (EXAMPLES_DIR, TEMPLATES_DIR):
        for path in sorted(guide_path.joinpath(*directory.parts).glob("*.xml")):
            for element in read_xml(path.name, path.read_bytes()).elements:
                attributes = element.attributes
                is_plain_ref = "ref" in attributes and "nameOfRefClass" not in attributes
                if is_plain_ref and element.name.endswith("Ref"):
                    names.setdefault(element.name, set()).add(path.name)
    return names


def test_every_entry_matches_the_xsd(guide_path: Path) -> None:
    """Jeder Eintrag nennt die XSD-Typen und alle laut XSD erlaubten Zieltypen (Entscheid A1).

    Die Zieltypen sind die Aufzählung `NameOfClass…RefStructureType` des Ref-Typs. Umfasst die XSD
    praktisch jede Klasse (Ober­begriff `PointInSequence`), steht in der Liste der praktische
    Zieltyp von Hand; diese Namen stehen in `UNRESTRICTED`.
    """
    xsd = load_xsd_refs(guide_path / "xsd" / "xsd")
    problems: list[str] = []
    for name, entry in _listed_refs().items():
        if sorted(xsd.type_names(name)) != sorted(entry["xsdTypes"]):
            problems.append(
                f"{name}: xsdTypes {entry['xsdTypes']} != {sorted(xsd.type_names(name))}"
            )
            continue
        allowed = xsd.targets(name)
        if allowed is None:
            problems.append(f"{name}: XSD nennt keine Zielklassen")
        elif len(allowed) > UNRESTRICTED_LIMIT:
            if name not in UNRESTRICTED:
                problems.append(
                    f"{name}: XSD erlaubt {len(allowed)} Klassen, Name fehlt in UNRESTRICTED"
                )
        elif sorted(entry["targets"]) != sorted({*allowed, *EXTRA_BEYOND_XSD.get(name, ())}):
            missing = sorted(set(allowed) - set(entry["targets"]))
            extra = sorted(set(entry["targets"]) - set(allowed) - EXTRA_BEYOND_XSD.get(name, set()))
            problems.append(f"{name}: fehlt {missing}, nicht in der XSD {extra}")
    assert problems == [], problems


def test_unrestricted_names_are_still_unrestricted(guide_path: Path) -> None:
    """Die Ausnahmeliste enthält nur Namen, bei denen die XSD tatsächlich jede Klasse erlaubt."""
    xsd = load_xsd_refs(guide_path / "xsd" / "xsd")
    for name in UNRESTRICTED:
        allowed = xsd.targets(name)
        assert allowed is not None
        assert len(allowed) > UNRESTRICTED_LIMIT, name


def test_every_guide_ref_name_is_listed_or_follows_from_its_name(guide_path: Path) -> None:
    """Beispiele und Vorlagen: Jeder Ref-Name steht in der Liste oder folgt aus dem Namen.

    Aus dem Namen ergibt sich der Zieltyp, wenn die XSD genau die Klasse „Name ohne `Ref`“ erlaubt.
    """
    xsd = load_xsd_refs(guide_path / "xsd" / "xsd")
    listed = _listed_refs()
    problems = []
    for name, files in _guide_ref_names(guide_path).items():
        if name in listed or name in GUIDE_WITHOUT_XSD:
            continue
        if xsd.targets(name) != (name.removesuffix("Ref"),):
            problems.append(f"{name} (z. B. {sorted(files)[0]}): XSD erlaubt {xsd.targets(name)}")
    assert problems == [], f"config/ref-targets.json ergänzen: {problems}"


def test_guide_names_without_xsd_declaration_are_still_undeclared(guide_path: Path) -> None:
    """Die Ausnahme gilt nur, solange die XSD den Namen nicht deklariert."""
    xsd = load_xsd_refs(guide_path / "xsd" / "xsd")
    for name in GUIDE_WITHOUT_XSD:
        assert xsd.type_names(name) == frozenset(), name
        assert name in _guide_ref_names(guide_path)


def test_no_example_reference_misses_a_list_entry(guide_path: Path) -> None:
    """Zeigt eine nicht aufgelöste Referenz auf eine ID anderen Typs, fehlt ein Listeneintrag.

    Ein Beispiel ohne Listeneintrag wäre sonst ein falscher Fehler (Entscheid „Zieltyp“); der Test
    nennt den Ref-Namen und den Typ, der in `config/ref-targets.json` zu ergänzen ist.
    """
    ref_targets = REF_TARGETS
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
