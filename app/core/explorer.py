"""Generischer Objekt-Explorer: Objektdetail mit Pfad und Eigenschaften, XML-Ausschnitt."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Final

from app.core.index.dataset_index import DatasetIndex, ElementRow

MAX_PROPERTY_NODES: Final = 2000
CONTEXT_LINES: Final = 30
MAX_WINDOW_LINES: Final = 2000


@dataclass
class PropertyNode:
    """Ein Element im Eigenschaftsbaum eines Objekts."""

    element: ElementRow
    children: list[PropertyNode] = field(default_factory=list)


@dataclass(frozen=True)
class ObjectDetail:
    """Objekt mit Frame, Pfad und Eigenschaften (Kindelemente als Baum)."""

    element: ElementRow
    frame: ElementRow | None
    path: str
    properties: list[PropertyNode]
    truncated: bool


@dataclass(frozen=True)
class FrameBand:
    """Zeilenbereich eines Frames im XML-Ausschnitt."""

    frame: ElementRow
    from_line: int
    to_line: int


@dataclass(frozen=True)
class XmlWindow:
    """Ausschnitt einer Datei mit markiertem Bereich.

    `focus_from`/`focus_to` sind Zeichen-Offsets relativ zu `text`.
    """

    file_id: int
    file_name: str
    first_line: int
    text: str
    focus_from: int
    focus_to: int
    frames: list[FrameBand]
    truncated: bool


def element_path(index: DatasetIndex, element: ElementRow) -> str:
    """Vollständiger Pfad, Positionsnummer nur bei gleichnamigen Geschwistern (`Line[3]`)."""
    parts: list[str] = []
    current: ElementRow | None = element
    while current is not None:
        position = ""
        if index.same_name_sibling_count(current) > 1:
            position = f"[{current.sibling_position}]"
        parts.append(current.name + position)
        current = None if current.parent_id is None else index.element(current.parent_id)
    return "/" + "/".join(reversed(parts))


def object_detail(index: DatasetIndex, element_id: int) -> ObjectDetail | None:
    """Objektdetail eines Elements; `None`, wenn es das Element nicht gibt."""
    element = index.element(element_id)
    if element is None:
        return None
    descendants = index.descendants(element_id, MAX_PROPERTY_NODES + 1)
    truncated = len(descendants) > MAX_PROPERTY_NODES
    nodes: dict[int, PropertyNode] = {}
    roots: list[PropertyNode] = []
    for row in descendants[:MAX_PROPERTY_NODES]:
        node = PropertyNode(row)
        nodes[row.id] = node
        parent = nodes.get(row.parent_id) if row.parent_id is not None else None
        if parent is not None:
            parent.children.append(node)
        elif row.parent_id == element_id:
            roots.append(node)
    frame = None if element.frame_id is None else index.element(element.frame_id)
    return ObjectDetail(element, frame, element_path(index, element), roots, truncated)


def xml_window(
    index: DatasetIndex, file_id: int, focus: tuple[int, int], focus_lines: tuple[int, int]
) -> XmlWindow | None:
    """Ausschnitt um einen Bereich (Zeichen-Offsets `focus`, Zeilen `focus_lines`)."""
    text = index.file_text(file_id)
    file_name = index.file_name(file_id)
    starts = index.line_starts(file_id)
    if text is None or file_name is None or starts is None:
        return None
    last_line = len(starts)
    first = max(1, min(focus_lines[0], last_line) - CONTEXT_LINES)
    last = min(last_line, max(focus_lines[1], focus_lines[0]) + CONTEXT_LINES)
    truncated = last - first + 1 > MAX_WINDOW_LINES
    if truncated:
        last = first + MAX_WINDOW_LINES - 1
    begin = starts[first - 1]
    finish = starts[last] - 1 if last < last_line else len(text)
    snippet = text[begin:finish]
    focus_from = min(max(focus[0] - begin, 0), len(snippet))
    focus_to = min(max(focus[1] - begin, focus_from), len(snippet))
    bands = []
    for frame in index.frames(file_id):
        frame_last = frame.end.line if frame.end is not None else last_line
        if frame.start.line <= last and frame_last >= first:
            bands.append(FrameBand(frame, max(frame.start.line, first), min(frame_last, last)))
    return XmlWindow(file_id, file_name, first, snippet, focus_from, focus_to, bands, truncated)


def element_xml_window(index: DatasetIndex, element_id: int) -> XmlWindow | None:
    """Ausschnitt mit dem markierten Element (bei fehlendem Ende nur der Anfang)."""
    element = index.element(element_id)
    if element is None:
        return None
    end = element.end or element.start
    return xml_window(
        index, element.file_id, (element.start.char, end.char), (element.start.line, end.line)
    )


def position_xml_window(
    index: DatasetIndex, file_id: int, line: int, column: int
) -> XmlWindow | None:
    """Ausschnitt um eine Stelle (Zeile, Spalte ab 1), z. B. einer Diagnose."""
    text = index.file_text(file_id)
    starts = index.line_starts(file_id)
    if text is None or starts is None:
        return None
    line = min(max(line, 1), len(starts))
    line_end = starts[line] - 1 if line < len(starts) else len(text)
    char = min(starts[line - 1] + max(column, 1) - 1, line_end)
    return xml_window(index, file_id, (char, char + 1), (line, line))


def _normalize_line_breaks(text: str) -> str:
    return text.replace("\r\n", "\n").replace("\r", "\n")


def _utf16_length(text: str) -> int:
    return len(text.encode("utf-16-le")) // 2


def editor_text(window: XmlWindow) -> tuple[str, int, int]:
    """Text und Markierung für einen Editor im Browser (CodeMirror).

    CodeMirror speichert jeden Zeilenumbruch als ein Zeichen (LF) und zählt in UTF-16-Einheiten;
    Python zählt Code-Points und behält CR LF. Ohne Umrechnung sässe die Markierung in Dateien mit
    CR LF oder mit Zeichen ausserhalb der Basisebene an der falschen Stelle.
    """
    text = window.text
    start = _utf16_length(_normalize_line_breaks(text[: window.focus_from]))
    end = _utf16_length(_normalize_line_breaks(text[: window.focus_to]))
    return _normalize_line_breaks(text), start, end
