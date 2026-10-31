"""Herkunftskette einer Angabe: Frame → enthaltende Objekte → Angabe → (bei Referenzen) Ziel.

Jedes Glied ist ein Element der Datei und damit bis zur Stelle im XML nachvollziehbar. Die Kette
zeigt, wo eine Angabe steht und, bei einer aufgelösten Referenz, wohin sie führt. Rechenketten für
abgeleitete Werte (Zeiten) folgen mit der Fahrtansicht (Phase 3).
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum

from app.core.index.dataset_index import DatasetIndex, ElementRow


class LinkKind(StrEnum):
    """Art eines Glieds der Herkunftskette."""

    FRAME = "frame"
    OBJECT = "object"
    ELEMENT = "element"
    """Eine Angabe, die selbst kein Objekt ist (Eigenschaft oder Ref-Element)."""
    TARGET = "target"
    """Das Ziel einer aufgelösten Referenz."""


@dataclass(frozen=True)
class ChainLink:
    """Ein Glied der Herkunftskette."""

    kind: LinkKind
    element: ElementRow


def _kind(element: ElementRow) -> LinkKind:
    if element.is_frame:
        return LinkKind.FRAME
    return LinkKind.OBJECT if element.xml_id else LinkKind.ELEMENT


def provenance_chain(index: DatasetIndex, element_id: int) -> list[ChainLink] | None:
    """Herkunftskette eines Elements; `None`, wenn es das Element nicht gibt."""
    element = index.element(element_id)
    if element is None:
        return None
    # Von der Angabe nach oben bis zum innersten Frame; darüber liegende Elemente gehören nicht
    # zur Herkunft (z. B. `CompositeFrame` ist ein eigener Frame).
    chain = [ChainLink(_kind(element), element)]
    current = element
    while current.parent_id is not None and not current.is_frame:
        parent = index.element(current.parent_id)
        if parent is None:
            break
        if parent.xml_id or parent.is_frame:
            chain.append(ChainLink(_kind(parent), parent))
        current = parent
    chain.reverse()
    reference = index.reference(element_id)
    if reference is not None and reference.target_id is not None:
        target = index.element(reference.target_id)
        if target is not None:
            chain.append(ChainLink(LinkKind.TARGET, target))
    return chain
