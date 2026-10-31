"""Referenzen (`…Ref`): erwartete Zieltypen, Auflösung über ID, Typ und Version.

Belege in docs/mapping.md (Abschnitt „Referenzen“), Entscheide in docs/decisions.md
(„Zieltyp von Referenzen“, „Nicht gefundenes Ziel einer Referenz“).

Der erwartete Zieltyp wird in dieser Reihenfolge bestimmt: `nameOfRefClass`, dann die Liste
`config/ref-targets.json`, dann der Name ohne `Ref`. `Quay` und `ScheduledStopPoint` mit gleicher ID
werden so unterschieden (docs/mapping.md, H6).

Dieses Modul kennt den Index nicht; der Index ruft es auf und speichert das Ergebnis.
"""

from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from app.core.index.dataset_index import DatasetIndex, ElementRow

REF_SUFFIX: Final = "Ref"
ANY_VERSION: Final = "any"


class ResolveStatus(StrEnum):
    """Ergebnis der Auflösung einer Referenz."""

    RESOLVED = "resolved"
    UNRESOLVED = "unresolved"
    """Objekte des erwarteten Typs sind vorhanden, die gesuchte `id` fehlt (Fehler)."""
    AMBIGUOUS = "ambiguous"
    """Mehrere Objekte passen (Warnung)."""
    EXTERNAL_OR_UNLOADED = "external_or_unloaded"
    """Der Datensatz enthält kein Objekt des erwarteten Typs; das Ziel steht vermutlich in einer
    anderen Datei (Hinweis)."""


@dataclass(frozen=True)
class Candidate:
    """Ein Objekt, das auf ID und erwarteten Typ passt."""

    element_id: int
    version: str | None


@dataclass(frozen=True)
class ReferenceRow:
    """Eine Referenz des Datensatzes mit Ergebnis der Auflösung.

    Attributes:
        element_id: das Ref-Element.
        owner_id: das Objekt (Element mit `id`), in dem die Referenz steht; `None` ausserhalb.
        target_ref: Wert des Attributs `ref`.
        ref_version: `version` bzw. `versionRef` der Referenz, falls vorhanden.
        expected: erwartete Zieltypen (Elementnamen).
        status: Ergebnis der Auflösung.
        target_id: das aufgelöste Objekt, nur bei `RESOLVED`.
    """

    element_id: int
    owner_id: int | None
    target_ref: str
    ref_version: str | None
    expected: tuple[str, ...]
    status: ResolveStatus
    target_id: int | None


@dataclass(frozen=True)
class ResolveResult:
    """Ergebnis: Status und, falls eindeutig, das Ziel."""

    status: ResolveStatus
    target: ElementRow | None = None


def is_reference(name: str, attributes: Mapping[str, str]) -> bool:
    """Referenz: Element mit `ref`, das `…Ref` heisst oder `nameOfRefClass` trägt."""
    if not attributes.get("ref"):
        return False
    if attributes.get("nameOfRefClass"):
        return True
    return name.endswith(REF_SUFFIX) and len(name) > len(REF_SUFFIX)


def expected_types(
    name: str, attributes: Mapping[str, str], ref_targets: Mapping[str, tuple[str, ...]]
) -> tuple[str, ...]:
    """Erwartete Zieltypen einer Referenz (leer, wenn das Element keine Referenz ist)."""
    if not is_reference(name, attributes):
        return ()
    declared = attributes.get("nameOfRefClass")
    if declared:
        return (declared,)
    listed = ref_targets.get(name)
    if listed:
        return listed
    return (name.removesuffix(REF_SUFFIX),)


def reference_version(attributes: Mapping[str, str]) -> str | None:
    """`version` oder `versionRef` einer Referenz; `None` ohne Angabe."""
    return attributes.get("version") or attributes.get("versionRef")


def classify(
    candidates: Sequence[Candidate], ref_version: str | None, type_present: bool
) -> tuple[ResolveStatus, int | None]:
    """Status und Ziel aus den passenden Objekten.

    Passen mehrere Objekte, entscheidet die Version der Referenz (ausser `any`); bleibt es bei
    mehreren, ist die Referenz mehrdeutig. Eine abweichende Version bei genau einem Objekt ändert
    nichts: Die ID und der Typ sind eindeutig, nichts wird verworfen oder ergänzt.
    """
    if not candidates:
        status = ResolveStatus.UNRESOLVED if type_present else ResolveStatus.EXTERNAL_OR_UNLOADED
        return status, None
    remaining = list(candidates)
    if len(remaining) > 1 and ref_version not in (None, ANY_VERSION):
        matching = [c for c in remaining if c.version == ref_version]
        remaining = matching or remaining
    if len(remaining) > 1:
        return ResolveStatus.AMBIGUOUS, None
    return ResolveStatus.RESOLVED, remaining[0].element_id


def resolve(index: DatasetIndex, ref_element: ElementRow) -> ResolveResult:
    """Ergebnis der Auflösung einer Referenz im Datensatz (beim Öffnen berechnet)."""
    row = index.reference(ref_element.id)
    if row is None:
        return ResolveResult(ResolveStatus.UNRESOLVED)
    target = None if row.target_id is None else index.element(row.target_id)
    return ResolveResult(row.status, target)
