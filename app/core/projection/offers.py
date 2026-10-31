"""Angebote (`ServiceFacilitySet`), Verkehrsmittel und Produktkategorie mit Stammdaten.

Belege in docs/mapping.md: A1 bis A4 (Angebote), V1 bis V4 (Verkehrsmittel, Produktkategorie).

- Ein `ServiceFacilitySet` enthält je Gruppe (z. B. `CateringFacilityList`, `FareClasses`) einen
  oder mehrere Codes, getrennt durch Leerraum. Jeder Code wird unverändert gezeigt; die Bedeutung
  kommt aus dem Blatt `Angebote` der Mappingtabelle (Spalte `Facility Value`).
- `TypeOfProductCategory`: Name und Kurzbezeichnung aus der Datei; zusätzlich die Zeile des Blatts
  `VMArt->NeTEx`, deren `Abk` gleich dem `ShortName` ist.
- `TransportMode` und `TransportSubmode` sind Codes ohne Erläuterung in den Stammdaten.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final

from app.core.guide.mapping import MappingTable
from app.core.index.dataset_index import DatasetIndex, ElementRow
from app.core.projection.common import (
    LangText,
    Lookup,
    LookupStatus,
    child,
    children,
    follow,
    multilingual,
    text_of,
)
from app.core.projection.master_data import MasterInfo, lookup_master

FACILITY_SHEET: Final = "Angebote"
FACILITY_COLUMN: Final = "Facility Value"
PRODUCT_SHEET: Final = "VMArt->NeTEx"
PRODUCT_COLUMN: Final = "Abk"
STOP_USE_SHEET: Final = "StopUse"
STOP_USE_COLUMN: Final = "Value"
# Kindelemente eines ServiceFacilitySet, die keine Liste von Angebots-Codes sind.
_NOT_FACILITY_CODES: Final = frozenset(
    {
        "Name",
        "ShortName",
        "Description",
        "Extensions",
        "keyList",
        "privateCodes",
        "PrivateCode",
        "validityConditions",
        "alternativeTexts",
        "accommodations",
    }
)


@dataclass(frozen=True)
class CodedValue:
    """Ein Code aus der Datei mit Herkunft und Bedeutung aus den Stammdaten."""

    code: str
    element: ElementRow
    master: MasterInfo | None = None
    """`None`: Für diesen Code sind keine Stammdaten vorgesehen."""


@dataclass(frozen=True)
class FacilityGroup:
    """Eine Gruppe von Angebots-Codes (z. B. `CateringFacilityList`)."""

    element: ElementRow
    codes: list[CodedValue]


@dataclass(frozen=True)
class FacilitySetView:
    """Ein `ServiceFacilitySet` hinter einer Referenz."""

    ref: ElementRow
    facility_set: ElementRow | None
    problem: Lookup | None
    description: list[LangText] = field(default_factory=list)
    groups: list[FacilityGroup] = field(default_factory=list)


@dataclass(frozen=True)
class TransportView:
    """Verkehrsmittel einer Fahrt oder Linie: `TransportMode` und `TransportSubmode`."""

    owner: ElementRow
    role: str
    """`journey` oder `line`."""
    mode: Lookup
    submode_type: str | None
    submode: Lookup


@dataclass(frozen=True)
class CategoryView:
    """`TypeOfProductCategory` hinter einer Referenz mit Name aus der Datei und Stammdaten."""

    role: str
    """`journey`, `line` oder `part`."""
    ref: ElementRow
    target: ElementRow | None
    problem: Lookup | None
    short_name: Lookup
    names: list[LangText]
    master: MasterInfo | None


def facility_set(index: DatasetIndex, ref: ElementRow, table: MappingTable) -> FacilitySetView:
    """Liest das `ServiceFacilitySet` hinter einer `ServiceFacilitySetRef`."""
    target, problem = follow(index, ref)
    if target is None:
        return FacilitySetView(ref, None, problem)
    groups = []
    for group in index.children(target.id):
        text = group.text.strip()
        if group.name in _NOT_FACILITY_CODES or not text or index.children(group.id):
            continue
        codes = [
            CodedValue(code, group, lookup_master(table, FACILITY_SHEET, FACILITY_COLUMN, code))
            for code in text.split()
        ]
        groups.append(FacilityGroup(group, codes))
    return FacilitySetView(
        ref, target, None, multilingual(index, child(index, target, "Description")), groups
    )


def facility_sets(
    index: DatasetIndex, owner: ElementRow, table: MappingTable
) -> list[FacilitySetView]:
    """Alle `ServiceFacilitySetRef` unter `facilities` eines Elements."""
    views: list[FacilitySetView] = []
    for container in children(index, owner, "facilities"):
        views.extend(
            facility_set(index, ref, table)
            for ref in children(index, container, "ServiceFacilitySetRef")
        )
    return views


def _submode(index: DatasetIndex, owner: ElementRow) -> tuple[str | None, Lookup]:
    container = child(index, owner, "TransportSubmode")
    if container is None:
        return None, Lookup(LookupStatus.ABSENT)
    for item in index.children(container.id):
        value = text_of(item)
        if value.text is not None:
            return item.name, value
    return None, Lookup(LookupStatus.ABSENT, None, container)


def transport(index: DatasetIndex, owner: ElementRow, role: str) -> TransportView:
    """`TransportMode` und `TransportSubmode` eines Elements, jeweils mit Quelle."""
    submode_type, submode = _submode(index, owner)
    return TransportView(
        owner, role, text_of(child(index, owner, "TransportMode")), submode_type, submode
    )


def category(
    index: DatasetIndex, owner: ElementRow, role: str, table: MappingTable
) -> CategoryView | None:
    """`TypeOfProductCategory` eines Elements; `None`, wenn es keine Referenz darauf trägt."""
    ref = child(index, owner, "TypeOfProductCategoryRef")
    if ref is None:
        return None
    target, problem = follow(index, ref)
    if target is None:
        return CategoryView(role, ref, None, problem, Lookup(LookupStatus.ABSENT), [], None)
    short_name = text_of(child(index, target, "ShortName"))
    master = (
        None
        if short_name.text is None
        else lookup_master(table, PRODUCT_SHEET, PRODUCT_COLUMN, short_name.text)
    )
    names = multilingual(index, child(index, target, "Name"))
    return CategoryView(role, ref, target, None, short_name, names, master)
