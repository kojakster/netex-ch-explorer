"""Gemeinsame Bausteine der Fahrten-Projektion: Angaben mit Herkunft und Navigation im Index.

Jede Angabe trägt das Element der Quelle, damit sie bis zur Stelle im XML nachvollziehbar bleibt.
Fehlt eine Angabe oder lässt sie sich nicht auflösen, steht der Grund da (nie ein Ersatzwert).
"""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from app.core.index.dataset_index import DatasetIndex, ElementRow
from app.core.index.references import ResolveStatus
from app.core.messages import MessageKey, ParamValue, Severity


class LookupStatus(StrEnum):
    """Ergebnis einer Angabe."""

    FOUND = "found"
    ABSENT = "absent"
    """Das Element fehlt in den Daten."""
    NOT_RESOLVED = "not_resolved"
    """Objekte des erwarteten Typs sind vorhanden, das gesuchte Ziel nicht (Fehler)."""
    EXTERNAL_OR_UNLOADED = "external_or_unloaded"
    """Der Datensatz enthält keine Objekte des erwarteten Typs (extern oder nicht geladen)."""
    AMBIGUOUS = "ambiguous"
    """Die Referenz passt auf mehrere Objekte."""


@dataclass(frozen=True)
class Lookup:
    """Eine Angabe mit Herkunft: Status, Text aus der Datei und Element der Quelle."""

    status: LookupStatus
    text: str | None = None
    element: ElementRow | None = None


@dataclass(frozen=True)
class LangText:
    """Ein Text aus der Datei mit Sprachkennzeichen (`lang`), unverändert."""

    lang: str | None
    text: str
    element: ElementRow


@dataclass(frozen=True)
class Finding:
    """Befund der Fahrtansicht: Schweregrad, Übersetzungsschlüssel, Parameter und Stelle.

    Als Grund steht er bei „nicht berechenbar“; als Diagnose (Art `projection`) in der Fahrtansicht.
    """

    severity: Severity
    key: MessageKey
    params: Mapping[str, ParamValue]
    element: ElementRow | None = None


ABSENT: Final = Lookup(LookupStatus.ABSENT)
_RESOLVE_TO_LOOKUP: Final = {
    ResolveStatus.UNRESOLVED: LookupStatus.NOT_RESOLVED,
    ResolveStatus.EXTERNAL_OR_UNLOADED: LookupStatus.EXTERNAL_OR_UNLOADED,
    ResolveStatus.AMBIGUOUS: LookupStatus.AMBIGUOUS,
}


def child(index: DatasetIndex, element: ElementRow, name: str) -> ElementRow | None:
    """Erstes direktes Kindelement mit diesem Namen."""
    return next((item for item in index.children(element.id) if item.name == name), None)


def children(index: DatasetIndex, element: ElementRow, name: str) -> list[ElementRow]:
    """Alle direkten Kindelemente mit diesem Namen in Dokumentreihenfolge."""
    return [item for item in index.children(element.id) if item.name == name]


def text_of(element: ElementRow | None) -> Lookup:
    """Textinhalt eines Elements (ohne umgebenden Leerraum) oder „fehlt“."""
    if element is None or not element.text.strip():
        return ABSENT
    return Lookup(LookupStatus.FOUND, element.text.strip(), element)


def follow(index: DatasetIndex, ref: ElementRow | None) -> tuple[ElementRow | None, Lookup | None]:
    """Löst eine Referenz auf; liefert das Ziel oder eine Angabe zum Grund."""
    if ref is None:
        return None, ABSENT
    result = index.resolve(ref)
    if result.target is not None:
        return result.target, None
    if result.status is ResolveStatus.RESOLVED:
        # Der Index liefert bei `RESOLVED` immer das Ziel; alles andere ist ein Programmfehler.
        message = f"Referenz {ref.id} ist aufgelöst, aber das Ziel fehlt"
        raise RuntimeError(message)
    return None, Lookup(_RESOLVE_TO_LOOKUP[result.status], ref.attributes.get("ref"), ref)


def follow_child(
    index: DatasetIndex, element: ElementRow | None, ref_name: str
) -> tuple[ElementRow | None, Lookup | None]:
    """Folgt dem Ref-Kindelement `ref_name` eines Elements (`None` = Element fehlt)."""
    ref = None if element is None else child(index, element, ref_name)
    return follow(index, ref)


def points_to(index: DatasetIndex, ref: ElementRow | None, target: ElementRow) -> bool:
    """Ob eine Referenz auf das Element zeigt.

    Aufgelöst entscheidet das Ziel; sonst gleicht die `id` im `ref`-Attribut (die Referenz ist
    dann nicht auflösbar, kann aber trotzdem gemeint sein).
    """
    if ref is None:
        return False
    result = index.resolve(ref)
    if result.target is not None:
        return result.target.id == target.id
    return target.xml_id is not None and ref.attributes.get("ref") == target.xml_id


def multilingual(index: DatasetIndex, element: ElementRow | None) -> list[LangText]:
    """Alle Fassungen eines mehrsprachigen Textes (`Name`, `Text`, `Description`).

    NeTEx 2.x kennt die verschachtelte Form (`<Text lang="de">…<Text lang="en">…</Text></Text>`);
    zuerst kommt der eigene Text des Elements, danach die verschachtelten `Text`-Elemente in
    Dokumentreihenfolge. Nichts wird übersetzt oder ergänzt.
    """
    if element is None:
        return []
    texts = []
    if element.text.strip():
        texts.append(LangText(element.attributes.get("lang"), element.text.strip(), element))
    for nested in children(index, element, "Text"):
        texts.extend(multilingual(index, nested))
    return texts
