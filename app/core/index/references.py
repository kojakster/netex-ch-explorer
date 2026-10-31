"""Auflösen einer Referenz (`…Ref`) über ID und erwarteten Typ.

Grundstufe für Phase 1 (Fahrtenliste). Der erwartete Typ kommt aus `nameOfRefClass` oder aus dem
Namen des Ref-Elements ohne `Ref`; `Quay` und `ScheduledStopPoint` mit gleicher ID werden so
unterschieden (docs/mapping.md, H6). Versionen, Rückwärtsreferenzen und der Status
`external_or_unloaded` folgen in Phase 2.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from app.core.index.dataset_index import DatasetIndex, ElementRow

REF_SUFFIX: Final = "Ref"


class ResolveStatus(StrEnum):
    """Ergebnis einer Auflösung."""

    RESOLVED = "resolved"
    NOT_FOUND = "not_found"
    AMBIGUOUS = "ambiguous"


@dataclass(frozen=True)
class ResolveResult:
    """Ergebnis: Status und, falls eindeutig, das Ziel."""

    status: ResolveStatus
    target: ElementRow | None = None


def expected_type(ref_element: ElementRow) -> str | None:
    """Erwarteter Zieltyp einer Referenz; `None`, wenn das Element keine Referenz ist."""
    declared = ref_element.attributes.get("nameOfRefClass")
    if declared:
        return declared
    if ref_element.name.endswith(REF_SUFFIX) and len(ref_element.name) > len(REF_SUFFIX):
        return ref_element.name.removesuffix(REF_SUFFIX)
    return None


def resolve(index: DatasetIndex, ref_element: ElementRow) -> ResolveResult:
    """Löst eine Referenz im Datensatz auf."""
    target_id = ref_element.attributes.get("ref")
    target_type = expected_type(ref_element)
    if not target_id or target_type is None:
        return ResolveResult(ResolveStatus.NOT_FOUND)
    candidates = index.objects_by_id(target_id, target_type)
    if not candidates:
        return ResolveResult(ResolveStatus.NOT_FOUND)
    if len(candidates) > 1:
        return ResolveResult(ResolveStatus.AMBIGUOUS)
    return ResolveResult(ResolveStatus.RESOLVED, candidates[0])
