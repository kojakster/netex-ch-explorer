"""Zieltypen von Referenzen laut NeTEx-XSD des Guide-Klons.

Die XSD nennt je Ref-Typ (`…RefStructure`) im Attribut `nameOfRefClass` eine Aufzählung
(`NameOfClass…RefStructureType`) aller konkreten Klassen, auf die die Referenz zeigen darf.
Ref-Elemente ohne eigenen `type` (nur `substitutionGroup`) erben den Typ ihres Kopfelements.
"""

from __future__ import annotations

import functools
from dataclasses import dataclass
from pathlib import Path

from app.core.reader.xml_reader import ElementRecord, read_xml

REF_SUFFIX = "Ref"
NAME_OF_CLASS_PREFIX = "NameOfClass"


@dataclass(frozen=True)
class XsdRefs:
    """Auszug der XSD: Ref-Elemente, Ref-Typen und ihre erlaubten Zielklassen."""

    element_types: dict[str, frozenset[str]]
    element_groups: dict[str, str]
    type_base: dict[str, str]
    type_class_enum: dict[str, str]
    enumerations: dict[str, tuple[str, ...]]

    def type_names(self, ref_name: str) -> frozenset[str]:
        """Ref-Typen, mit denen die XSD das Element deklariert (inkl. Kopfelement)."""
        name = ref_name
        seen: set[str] = set()
        while name not in self.element_types and name in self.element_groups and name not in seen:
            seen.add(name)
            name = self.element_groups[name]
        return self.element_types.get(name, frozenset())

    def targets(self, ref_name: str) -> tuple[str, ...] | None:
        """Alle erlaubten Zielklassen; `None`, wenn die XSD keine Aufzählung nennt."""
        types = self.type_names(ref_name)
        if not types:
            return None
        found: set[str] = set()
        for type_name in types:
            enum = self._enumeration(type_name)
            if enum is None:
                return None
            found.update(enum)
        return tuple(sorted(found))

    def _enumeration(self, type_name: str | None) -> tuple[str, ...] | None:
        while type_name:
            if type_name in self.type_class_enum:
                return self.enumerations.get(self.type_class_enum[type_name])
            type_name = self.type_base.get(type_name)
        return None


def _named(elements: list[ElementRecord], name: str) -> list[int]:
    return [i for i, element in enumerate(elements) if element.name == name]


def _inside(elements: list[ElementRecord], start: int) -> list[ElementRecord]:
    """Nachfahren des Elements an Position `start` (Dokumentreihenfolge)."""
    depth = elements[start].depth
    found = []
    for element in elements[start + 1 :]:
        if element.depth <= depth:
            break
        found.append(element)
    return found


def _add_ref_elements(
    elements: list[ElementRecord], refs: dict[str, set[str]], groups: dict[str, str]
) -> None:
    for element in elements:
        name = element.attributes.get("name", "")
        if element.name != "element" or not name.endswith(REF_SUFFIX):
            continue
        if "type" in element.attributes:
            refs.setdefault(name, set()).add(element.attributes["type"])
        if "substitutionGroup" in element.attributes:
            groups[name] = element.attributes["substitutionGroup"]


def _add_ref_types(
    elements: list[ElementRecord], bases: dict[str, str], class_enums: dict[str, str]
) -> None:
    for position in _named(elements, "complexType"):
        name = elements[position].attributes.get("name")
        if not name:
            continue
        inside = _inside(elements, position)
        for derivation in inside:
            if derivation.name in ("restriction", "extension") and "base" in derivation.attributes:
                bases[name] = derivation.attributes["base"]
                break
        for attribute in inside:
            if (
                attribute.name == "attribute"
                and attribute.attributes.get("name") == "nameOfRefClass"
            ):
                class_enums[name] = attribute.attributes.get("type", "")


def _add_enumerations(
    elements: list[ElementRecord], enumerations: dict[str, tuple[str, ...]]
) -> None:
    for position in _named(elements, "simpleType"):
        name = elements[position].attributes.get("name", "")
        if name.startswith(NAME_OF_CLASS_PREFIX):
            enumerations[name] = tuple(
                value.attributes.get("value", "")
                for value in _inside(elements, position)
                if value.name == "enumeration"
            )


@functools.cache
def load_xsd_refs(xsd_dir: Path) -> XsdRefs:
    """Liest alle XSD-Dateien unter `xsd_dir` (zwischengespeichert)."""
    element_types: dict[str, set[str]] = {}
    element_groups: dict[str, str] = {}
    type_base: dict[str, str] = {}
    type_class_enum: dict[str, str] = {}
    enumerations: dict[str, tuple[str, ...]] = {}
    for path in sorted(xsd_dir.rglob("*.xsd")):
        parsed = read_xml(path.name, path.read_bytes())
        _add_ref_elements(parsed.elements, element_types, element_groups)
        _add_ref_types(parsed.elements, type_base, type_class_enum)
        _add_enumerations(parsed.elements, enumerations)
    return XsdRefs(
        {name: frozenset(types) for name, types in element_types.items()},
        element_groups,
        type_base,
        type_class_enum,
        enumerations,
    )
