"""Objektbaum: Objekte (Elemente mit `id`) nach Frames gegliedert und eingerückt."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.core.index.dataset_index import DatasetIndex, ElementRow

# Obergrenze der zurückgegebenen Treffer (Frames eingeschlossen); darüber wird gekürzt und gemeldet.
MAX_TREE_OBJECTS: Final = 5000


@dataclass(frozen=True)
class TreeEntry:
    """Ein Eintrag des Baums in Dokumentreihenfolge; `depth` 0 ist die oberste Ebene.

    `matches` ist `False` bei Vorfahren, die nur den Zusammenhang eines Treffers zeigen
    (nur bei aktivem Filter).
    """

    element: ElementRow
    depth: int
    matches: bool


@dataclass(frozen=True)
class ObjectTree:
    """Baum als flache Liste in Vorordnung.

    `entries` enthält die Frames (Kopfzeilen, verschachtelte Frames eine Ebene tiefer) mit ihren
    Objekten, `outside` die Objekte ausserhalb jedes Frames. `total` sind alle Treffer, `shown`
    die zurückgegebenen; bei `truncated` wurde gekürzt.
    """

    entries: list[TreeEntry]
    outside: list[TreeEntry]
    total: int
    shown: int
    truncated: bool


def _is_container(element: ElementRow) -> bool:
    """Frames und Objekte (Elemente mit `id`) gliedern den Baum; alle anderen Elemente nicht."""
    return element.is_frame or element.xml_id is not None


def _containers(
    index: DatasetIndex, elements: list[ElementRow], lookup: dict[int, ElementRow]
) -> dict[int, int | None]:
    """Nächstes übergeordnetes Frame bzw. Objekt je Element (`None`: es gibt keines).

    Holt die Vorfahren ebenenweise für alle Elemente zugleich, nicht je Element einzeln.
    """
    containers: dict[int, int | None] = {}
    cursors = {element.id: element.parent_id for element in elements}
    while cursors:
        wanted = [cursor for cursor in cursors.values() if cursor is not None]
        lookup.update(index.elements_by_ids([cursor for cursor in wanted if cursor not in lookup]))
        upwards: dict[int, int | None] = {}
        for element_id, cursor in cursors.items():
            ancestor = None if cursor is None else lookup.get(cursor)
            if ancestor is None:
                containers[element_id] = None
            elif _is_container(ancestor):
                containers[element_id] = ancestor.id
            else:
                upwards[element_id] = ancestor.parent_id
        cursors = upwards
    return containers


def _flatten(
    roots: list[int],
    children: dict[int, list[int]],
    placed: dict[int, ElementRow],
    matched: set[int],
    base_depth: int,
) -> list[TreeEntry]:
    """Vorordnung ohne Rekursion (beliebig tiefe Verschachtelung)."""
    entries: list[TreeEntry] = []
    stack = [(root, base_depth) for root in reversed(roots)]
    while stack:
        element_id, depth = stack.pop()
        entries.append(TreeEntry(placed[element_id], depth, element_id in matched))
        stack.extend((child, depth + 1) for child in reversed(children.get(element_id, [])))
    return entries


def build_object_tree(
    index: DatasetIndex,
    object_type: str | None,
    query: str | None,
    limit: int = MAX_TREE_OBJECTS,
) -> ObjectTree:
    """Baum der Objekte, die Typ und Teiltext (ID oder Name) entsprechen.

    Jeder Treffer erscheint unter seinem nächsten übergeordneten Objekt bzw. Frame; diese
    Vorfahren kommen auch ohne eigenen Treffer hinzu (`matches=False`). Frames sind Kopfzeilen.
    Es werden höchstens `limit` Treffer berücksichtigt. Alle Abfragen laufen ebenenweise.
    """
    total, hits = index.search_objects(object_type, query, limit, 0)
    matched = {hit.id for hit in hits}
    placed: dict[int, ElementRow] = {hit.id: hit for hit in hits}
    lookup: dict[int, ElementRow] = dict(placed)
    container_of: dict[int, int | None] = {}
    pending = list(hits)
    while pending:
        found = _containers(index, pending, lookup)
        container_of.update(found)
        pending = []
        for new_id in dict.fromkeys(c for c in found.values() if c is not None):
            if new_id not in placed:
                placed[new_id] = lookup[new_id]
                pending.append(lookup[new_id])
    children: dict[int, list[int]] = {}
    frame_roots: list[int] = []
    outside_roots: list[int] = []
    for element_id in sorted(placed):
        element = placed[element_id]
        container_id = container_of[element_id]
        container = None if container_id is None else placed[container_id]
        if container is None or (element.is_frame and not container.is_frame):
            (frame_roots if element.is_frame else outside_roots).append(element_id)
        else:
            children.setdefault(container.id, []).append(element_id)
    return ObjectTree(
        entries=_flatten(frame_roots, children, placed, matched, 0),
        outside=_flatten(outside_roots, children, placed, matched, 0),
        total=total,
        shown=len(hits),
        truncated=total > len(hits),
    )
