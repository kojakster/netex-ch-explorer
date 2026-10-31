"""Index eines Datensatzes: SQLite im Arbeitsspeicher mit allen Elementen.

Entscheid „Index: alle Elemente im Arbeitsspeicher“ (docs/decisions.md): Jedes Element wird mit
Position, Eltern, Frame und Pfadform gespeichert. Die Pfadform (ohne Positionsnummern) steht
einmal in `path_shapes`; der vollständige Pfad mit Positionsnummern wird beim Anzeigen berechnet.

Frames: Ein Element ist ein Frame, wenn sein Name auf `Frame` endet und es direkt in `frames`
oder `dataObjects` steht. Jedes Element gehört zum innersten Frame, in dem es steht.
Grau: Ein Element ist „für den Fahrplan nicht relevant“, wenn es selbst oder ein Vorfahre in der
Grau-Liste steht.
Referenzen: Nach dem Einlesen aller Dateien wird jede Referenz (`…Ref` mit `ref`, auch in
`Extensions`) über ID, erwarteten Typ und Version aufgelöst; das Ergebnis steht in `refs`, nicht
Aufgelöstes zusätzlich als Diagnose (Art `reference`).
"""

from __future__ import annotations

import json
import sqlite3
import threading
from collections.abc import Iterable, Mapping, Sequence
from dataclasses import dataclass
from typing import Any, Final

from app.core.diagnostics import Diagnostic, DiagnosticCategory
from app.core.index.references import (
    Candidate,
    ReferenceRow,
    ResolveStatus,
    classify,
    differing_version,
    expected_types,
    is_reference,
    reference_version,
)
from app.core.messages import MessageKey, Severity
from app.core.positions import Position
from app.core.reader.xml_reader import ParsedFile

FRAME_CONTAINERS: Final = frozenset({"frames", "dataObjects"})
FRAME_SUFFIX: Final = "Frame"

_SCHEMA: Final = """
CREATE TABLE files (
    id INTEGER PRIMARY KEY,
    name TEXT NOT NULL,
    size INTEGER NOT NULL,
    sha256 TEXT NOT NULL,
    text TEXT NOT NULL,
    readable INTEGER NOT NULL
);
CREATE TABLE path_shapes (
    id INTEGER PRIMARY KEY,
    shape TEXT NOT NULL UNIQUE
);
CREATE TABLE elements (
    id INTEGER PRIMARY KEY,
    file_id INTEGER NOT NULL REFERENCES files(id),
    parent_id INTEGER REFERENCES elements(id),
    depth INTEGER NOT NULL,
    namespace TEXT,
    name TEXT NOT NULL,
    attributes TEXT NOT NULL,
    text TEXT NOT NULL,
    xml_id TEXT,
    version TEXT,
    label TEXT,
    search_id TEXT,
    search_label TEXT,
    start_byte INTEGER NOT NULL,
    start_char INTEGER NOT NULL,
    start_line INTEGER NOT NULL,
    start_column INTEGER NOT NULL,
    end_byte INTEGER,
    end_char INTEGER,
    end_line INTEGER,
    end_column INTEGER,
    is_frame INTEGER NOT NULL,
    frame_id INTEGER REFERENCES elements(id),
    not_relevant INTEGER NOT NULL,
    path_shape_id INTEGER NOT NULL REFERENCES path_shapes(id),
    sibling_position INTEGER NOT NULL
);
CREATE INDEX elements_xml_id ON elements(xml_id);
CREATE INDEX elements_name ON elements(name);
CREATE INDEX elements_parent ON elements(parent_id);
CREATE TABLE refs (
    element_id INTEGER PRIMARY KEY REFERENCES elements(id),
    owner_id INTEGER REFERENCES elements(id),
    target_ref TEXT NOT NULL,
    ref_version TEXT,
    expected TEXT NOT NULL,
    status TEXT NOT NULL,
    target_id INTEGER REFERENCES elements(id)
);
CREATE INDEX refs_owner ON refs(owner_id);
CREATE INDEX refs_target ON refs(target_id);
CREATE TABLE diagnostics (
    id INTEGER PRIMARY KEY,
    file_id INTEGER NOT NULL REFERENCES files(id),
    category TEXT NOT NULL,
    severity TEXT NOT NULL,
    key TEXT NOT NULL,
    params TEXT NOT NULL,
    byte INTEGER,
    char INTEGER,
    line INTEGER,
    column INTEGER
);
"""

_ELEMENT_COLUMNS: Final = (
    "e.id, e.file_id, f.name, e.parent_id, e.depth, e.namespace, e.name, e.attributes, e.text, "
    "e.xml_id, e.version, e.label, e.start_byte, e.start_char, e.start_line, e.start_column, "
    "e.end_byte, e.end_char, e.end_line, e.end_column, e.is_frame, e.frame_id, e.not_relevant, "
    "e.sibling_position"
)
_REFERENCE_SEVERITY: Final = {
    ResolveStatus.UNRESOLVED: Severity.ERROR,
    ResolveStatus.AMBIGUOUS: Severity.WARNING,
    ResolveStatus.EXTERNAL_OR_UNLOADED: Severity.INFO,
}
_REFERENCE_KEY: Final = {
    ResolveStatus.UNRESOLVED: MessageKey.REFERENCE_UNRESOLVED,
    ResolveStatus.AMBIGUOUS: MessageKey.REFERENCE_AMBIGUOUS,
    ResolveStatus.EXTERNAL_OR_UNLOADED: MessageKey.REFERENCE_EXTERNAL_OR_UNLOADED,
}
_MAX_PLACEHOLDERS: Final = 500
_REFERENCE_COLUMNS: Final = (
    "element_id, owner_id, target_ref, ref_version, expected, status, target_id"
)
_ELEMENT_SELECT: Final = (
    f"SELECT {_ELEMENT_COLUMNS} FROM elements e JOIN files f ON f.id = e.file_id"
)


@dataclass(frozen=True)
class FileSummary:
    """Eine Datei des Datensatzes."""

    id: int
    name: str
    size: int
    sha256: str
    readable: bool
    elements: int
    objects: int


@dataclass(frozen=True)
class ElementRow:
    """Ein Element aus dem Index."""

    id: int
    file_id: int
    file_name: str
    parent_id: int | None
    depth: int
    namespace: str | None
    name: str
    attributes: dict[str, str]
    text: str
    xml_id: str | None
    version: str | None
    label: str | None
    start: Position
    end: Position | None
    is_frame: bool
    frame_id: int | None
    not_relevant: bool
    sibling_position: int


@dataclass(frozen=True)
class ResolveResult:
    """Ergebnis der Auflösung einer Referenz: Status und, falls eindeutig, das Ziel."""

    status: ResolveStatus
    target: ElementRow | None = None


@dataclass(frozen=True)
class _PendingReference:
    """Eine Referenz, die nach dem Einlesen aller Dateien aufgelöst wird."""

    element_id: int
    file_id: int
    owner_id: int | None
    name: str
    attributes: dict[str, str]
    position: Position


@dataclass(frozen=True)
class IndexedDiagnostic:
    """Eine Diagnose mit Datei."""

    file_id: int
    file_name: str
    diagnostic: Diagnostic


def _row_to_element(row: Sequence[Any]) -> ElementRow:
    end = None if row[16] is None else Position(row[16], row[17], row[18], row[19])
    return ElementRow(
        id=row[0],
        file_id=row[1],
        file_name=row[2],
        parent_id=row[3],
        depth=row[4],
        namespace=row[5],
        name=row[6],
        attributes=json.loads(row[7]),
        text=row[8],
        xml_id=row[9],
        version=row[10],
        label=row[11],
        start=Position(row[12], row[13], row[14], row[15]),
        end=end,
        is_frame=bool(row[20]),
        frame_id=row[21],
        not_relevant=bool(row[22]),
        sibling_position=row[23],
    )


def _row_to_reference(row: Sequence[Any]) -> ReferenceRow:
    return ReferenceRow(
        element_id=row[0],
        owner_id=row[1],
        target_ref=row[2],
        ref_version=row[3],
        expected=tuple(json.loads(row[4])),
        status=ResolveStatus(row[5]),
        target_id=row[6],
    )


def _label(parsed: ParsedFile, children: dict[int, list[int]], index: int) -> str | None:
    """Anzeigename eines Objekts: Text des ersten direkten `Name`, sonst dessen erstes `Text`."""
    for child_index in children.get(index, ()):
        child = parsed.elements[child_index]
        if child.name != "Name":
            continue
        if child.text.strip():
            return child.text.strip()
        for grandchild_index in children.get(child_index, ()):
            grandchild = parsed.elements[grandchild_index]
            if grandchild.name == "Text" and grandchild.text.strip():
                return grandchild.text.strip()
        return None
    return None


class DatasetIndex:
    """Index aller Elemente eines Datensatzes; Abfragen sind threadsicher."""

    def __init__(
        self,
        files: Iterable[ParsedFile],
        not_relevant: Iterable[str],
        ref_targets: Mapping[str, tuple[str, ...]],
    ) -> None:
        self._lock = threading.Lock()
        # Ein Index gehört zu einem Datensatz; Zugriffe aus mehreren Threads schützt das Lock.
        self._db = sqlite3.connect(":memory:", check_same_thread=False)
        self._db.executescript(_SCHEMA)
        self._not_relevant = frozenset(not_relevant)
        self._ref_targets = ref_targets
        self._pending_references: list[_PendingReference] = []
        self._next_element_id = 1
        self._line_starts: dict[int, list[int]] = {}
        for file_id, parsed in enumerate(files, start=1):
            self._add_file(file_id, parsed)
        self._resolve_references()
        self._db.commit()

    def close(self) -> None:
        """Gibt den Speicher des Index frei."""
        with self._lock:
            self._db.close()

    def _path_shape_id(self, shape: str) -> int:
        row = self._db.execute("SELECT id FROM path_shapes WHERE shape = ?", (shape,)).fetchone()
        if row is not None:
            return int(row[0])
        cursor = self._db.execute("INSERT INTO path_shapes(shape) VALUES (?)", (shape,))
        return int(cursor.lastrowid or 0)

    def _add_file(self, file_id: int, parsed: ParsedFile) -> None:
        self._db.execute(
            "INSERT INTO files(id, name, size, sha256, text, readable) VALUES (?, ?, ?, ?, ?, ?)",
            (file_id, parsed.name, parsed.size, parsed.sha256, parsed.text, int(parsed.readable)),
        )
        offset = self._next_element_id
        children: dict[int, list[int]] = {}
        for record in parsed.elements:
            if record.parent is not None:
                children.setdefault(record.parent, []).append(record.index)
        shapes: list[str] = []
        frames: list[int | None] = []
        gray: list[bool] = []
        owners: list[int | None] = []
        sibling_counts: dict[tuple[int | None, str], int] = {}
        rows = []
        for record in parsed.elements:
            parent = record.parent
            parent_record = None if parent is None else parsed.elements[parent]
            shape = ("" if parent is None else shapes[parent]) + "/" + record.name
            shapes.append(shape)
            is_frame = (
                record.name.endswith(FRAME_SUFFIX)
                and parent_record is not None
                and parent_record.name in FRAME_CONTAINERS
            )
            inherited_frame = None if parent is None else frames[parent]
            frames.append(offset + record.index if is_frame else inherited_frame)
            gray.append(record.name in self._not_relevant or (parent is not None and gray[parent]))
            sibling_key = (parent, record.name)
            sibling_counts[sibling_key] = sibling_counts.get(sibling_key, 0) + 1
            xml_id = record.attributes.get("id")
            inherited_owner = None if parent is None else owners[parent]
            owners.append(offset + record.index if xml_id else inherited_owner)
            if is_reference(record.name, record.attributes):
                self._pending_references.append(
                    _PendingReference(
                        offset + record.index,
                        file_id,
                        inherited_owner,
                        record.name,
                        record.attributes,
                        record.start,
                    )
                )
            label = _label(parsed, children, record.index) if xml_id else None
            end = record.end
            rows.append(
                (
                    offset + record.index,
                    file_id,
                    None if parent is None else offset + parent,
                    record.depth,
                    record.namespace,
                    record.name,
                    json.dumps(record.attributes, ensure_ascii=False),
                    record.text,
                    xml_id,
                    record.attributes.get("version"),
                    label,
                    None if xml_id is None else xml_id.casefold(),
                    None if label is None else label.casefold(),
                    record.start.byte,
                    record.start.char,
                    record.start.line,
                    record.start.column,
                    None if end is None else end.byte,
                    None if end is None else end.char,
                    None if end is None else end.line,
                    None if end is None else end.column,
                    int(is_frame),
                    frames[-1],
                    int(gray[-1]),
                    self._path_shape_id(shape),
                    sibling_counts[sibling_key],
                )
            )
        self._db.executemany(
            "INSERT INTO elements VALUES (" + ", ".join(["?"] * 26) + ")",
            rows,
        )
        self._next_element_id = offset + len(parsed.elements)
        for diagnostic in parsed.diagnostics:
            self._insert_diagnostic(file_id, diagnostic)

    def _resolve_references(self) -> None:
        """Löst alle Referenzen auf, nachdem alle Dateien im Index stehen."""
        type_present: dict[tuple[str, ...], bool] = {}
        for pending in self._pending_references:
            types = expected_types(pending.name, pending.attributes, self._ref_targets)
            target_ref = pending.attributes["ref"]
            ref_version = reference_version(pending.attributes)
            placeholders = ", ".join("?" * len(types))
            candidates = [
                Candidate(row[0], row[1])
                for row in self._db.execute(
                    "SELECT id, version FROM elements"
                    f" WHERE xml_id = ? AND name IN ({placeholders}) ORDER BY id",
                    (target_ref, *types),
                )
            ]
            if types not in type_present:
                type_present[types] = (
                    self._db.execute(
                        "SELECT 1 FROM elements WHERE xml_id IS NOT NULL"
                        f" AND name IN ({placeholders}) LIMIT 1",
                        types,
                    ).fetchone()
                    is not None
                )
            status, target_id = classify(candidates, ref_version, type_present[types])
            if target_id is not None:
                found_version = differing_version(candidates, target_id, ref_version)
                if found_version is not None:
                    self._insert_version_hint(pending, ref_version, found_version)
            self._db.execute(
                "INSERT INTO refs VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    pending.element_id,
                    pending.owner_id,
                    target_ref,
                    ref_version,
                    json.dumps(types),
                    status,
                    target_id,
                ),
            )
            if status is not ResolveStatus.RESOLVED:
                self._insert_diagnostic(
                    pending.file_id,
                    Diagnostic(
                        DiagnosticCategory.REFERENCE,
                        _REFERENCE_SEVERITY[status],
                        _REFERENCE_KEY[status],
                        {
                            "element": pending.name,
                            "ref": target_ref,
                            "expected": ", ".join(types),
                        },
                        pending.position,
                    ),
                )
        self._pending_references = []

    def _insert_version_hint(
        self, pending: _PendingReference, ref_version: str | None, found_version: str
    ) -> None:
        self._insert_diagnostic(
            pending.file_id,
            Diagnostic(
                DiagnosticCategory.REFERENCE,
                Severity.INFO,
                MessageKey.REFERENCE_VERSION_DIFFERS,
                {
                    "element": pending.name,
                    "ref": pending.attributes["ref"],
                    "version": ref_version or "",
                    "found": found_version,
                },
                pending.position,
            ),
        )

    def _insert_diagnostic(self, file_id: int, diagnostic: Diagnostic) -> None:
        position = diagnostic.position
        self._db.execute(
            "INSERT INTO diagnostics(file_id, category, severity, key, params, byte, char, line,"
            " column) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (
                file_id,
                diagnostic.category,
                diagnostic.severity,
                diagnostic.key,
                json.dumps(diagnostic.params, ensure_ascii=False),
                None if position is None else position.byte,
                None if position is None else position.char,
                None if position is None else position.line,
                None if position is None else position.column,
            ),
        )

    # Abfragen

    def files(self) -> list[FileSummary]:
        """Alle Dateien mit Anzahl Elemente und Objekte."""
        with self._lock:
            rows = self._db.execute(
                "SELECT f.id, f.name, f.size, f.sha256, f.readable, COUNT(e.id), COUNT(e.xml_id)"
                " FROM files f LEFT JOIN elements e ON e.file_id = f.id GROUP BY f.id ORDER BY f.id"
            ).fetchall()
        return [FileSummary(r[0], r[1], r[2], r[3], bool(r[4]), r[5], r[6]) for r in rows]

    def file_name(self, file_id: int) -> str | None:
        """Name einer Datei."""
        with self._lock:
            row = self._db.execute("SELECT name FROM files WHERE id = ?", (file_id,)).fetchone()
        return None if row is None else str(row[0])

    def line_starts(self, file_id: int) -> list[int] | None:
        """Zeichen-Offsets der Zeilenanfänge (einmal berechnet, dann zwischengespeichert)."""
        cached = self._line_starts.get(file_id)
        if cached is not None:
            return cached
        text = self.file_text(file_id)
        if text is None:
            return None
        starts = [0]
        position = text.find("\n")
        while position >= 0:
            starts.append(position + 1)
            position = text.find("\n", position + 1)
        with self._lock:
            self._line_starts[file_id] = starts
        return starts

    def file_text(self, file_id: int) -> str | None:
        """Text einer Datei (ohne BOM)."""
        with self._lock:
            row = self._db.execute("SELECT text FROM files WHERE id = ?", (file_id,)).fetchone()
        return None if row is None else str(row[0])

    def object_types(self) -> list[tuple[str, int]]:
        """Objekttypen (Elementnamen mit `id`) und ihre Anzahl, alphabetisch."""
        with self._lock:
            rows = self._db.execute(
                "SELECT name, COUNT(*) FROM elements WHERE xml_id IS NOT NULL"
                " GROUP BY name ORDER BY name"
            ).fetchall()
        return [(name, count) for name, count in rows]

    def search_objects(
        self, object_type: str | None, query: str | None, limit: int, offset: int
    ) -> tuple[int, list[ElementRow]]:
        """Objekte nach Typ und Teiltext in ID oder Name (ohne Gross-/Kleinschreibung)."""
        conditions = ["e.xml_id IS NOT NULL"]
        params: list[object] = []
        if object_type:
            conditions.append("e.name = ?")
            params.append(object_type)
        if query:
            # instr statt LIKE: keine Platzhalterzeichen; Gross-/Kleinschreibung über casefold
            # (SQLite-LIKE gleicht nur ASCII an).
            conditions.append("(instr(e.search_id, ?) > 0 OR instr(e.search_label, ?) > 0)")
            params.extend([query.casefold(), query.casefold()])
        where = " WHERE " + " AND ".join(conditions)
        with self._lock:
            total = int(
                self._db.execute(
                    "SELECT COUNT(*) FROM elements e" + where,
                    params,
                ).fetchone()[0]
            )
            rows = self._db.execute(
                _ELEMENT_SELECT + where + " ORDER BY e.id LIMIT ? OFFSET ?",
                [*params, limit, offset],
            ).fetchall()
        return total, [_row_to_element(row) for row in rows]

    def element(self, element_id: int) -> ElementRow | None:
        """Ein Element über seine Index-Nummer."""
        with self._lock:
            row = self._db.execute(_ELEMENT_SELECT + " WHERE e.id = ?", (element_id,)).fetchone()
        return None if row is None else _row_to_element(row)

    def children(self, element_id: int) -> list[ElementRow]:
        """Direkte Kindelemente in Dokumentreihenfolge."""
        with self._lock:
            rows = self._db.execute(
                _ELEMENT_SELECT + " WHERE e.parent_id = ? ORDER BY e.id", (element_id,)
            ).fetchall()
        return [_row_to_element(row) for row in rows]

    def descendants(self, element_id: int, limit: int) -> list[ElementRow]:
        """Alle Nachfahren in Dokumentreihenfolge, höchstens `limit`.

        Nachfahren sind die direkt folgenden Elemente mit grösserer Tiefe; das gilt auch für
        Elemente ohne Ende (Datei mit Syntaxfehler).
        """
        element = self.element(element_id)
        if element is None:
            return []
        with self._lock:
            boundary = self._db.execute(
                "SELECT MIN(id) FROM elements WHERE file_id = ? AND id > ? AND depth <= ?",
                (element.file_id, element.id, element.depth),
            ).fetchone()[0]
            rows = self._db.execute(
                _ELEMENT_SELECT
                + " WHERE e.file_id = ? AND e.id > ?"
                + ("" if boundary is None else " AND e.id < ?")
                + " ORDER BY e.id LIMIT ?",
                (element.file_id, element.id, *(() if boundary is None else (boundary,)), limit),
            ).fetchall()
        return [_row_to_element(row) for row in rows]

    def resolve(self, ref_element: ElementRow) -> ResolveResult:
        """Ergebnis der Auflösung einer Referenz (beim Öffnen berechnet): Status und Ziel."""
        row = self.reference(ref_element.id)
        if row is None:
            return ResolveResult(ResolveStatus.UNRESOLVED)
        target = None if row.target_id is None else self.element(row.target_id)
        return ResolveResult(row.status, target)

    def reference(self, element_id: int) -> ReferenceRow | None:
        """Die Referenz eines Ref-Elements; `None`, wenn das Element keine Referenz ist."""
        with self._lock:
            row = self._db.execute(
                f"SELECT {_REFERENCE_COLUMNS} FROM refs WHERE element_id = ?", (element_id,)
            ).fetchone()
        return None if row is None else _row_to_reference(row)

    def references_of(self, owner_id: int, limit: int) -> list[ReferenceRow]:
        """Ausgehende Referenzen eines Objekts in Dokumentreihenfolge, höchstens `limit`."""
        with self._lock:
            rows = self._db.execute(
                f"SELECT {_REFERENCE_COLUMNS} FROM refs WHERE owner_id = ?"
                " ORDER BY element_id LIMIT ?",
                (owner_id, limit),
            ).fetchall()
        return [_row_to_reference(row) for row in rows]

    def references_to(self, target_id: int, limit: int) -> list[ReferenceRow]:
        """Eingehende (rückwärtige) Referenzen auf ein Objekt, höchstens `limit`."""
        with self._lock:
            rows = self._db.execute(
                f"SELECT {_REFERENCE_COLUMNS} FROM refs WHERE target_id = ?"
                " ORDER BY element_id LIMIT ?",
                (target_id, limit),
            ).fetchall()
        return [_row_to_reference(row) for row in rows]

    def references_among(self, element_ids: Sequence[int]) -> dict[int, ReferenceRow]:
        """Die Referenzen unter den angegebenen Elementen, nach Element-Nummer."""
        found: dict[int, ReferenceRow] = {}
        # In Stapeln: ältere SQLite-Versionen erlauben höchstens 999 Platzhalter je Abfrage.
        for start in range(0, len(element_ids), _MAX_PLACEHOLDERS):
            batch = list(element_ids[start : start + _MAX_PLACEHOLDERS])
            placeholders = ", ".join("?" * len(batch))
            with self._lock:
                rows = self._db.execute(
                    f"SELECT {_REFERENCE_COLUMNS} FROM refs WHERE element_id IN ({placeholders})",
                    batch,
                ).fetchall()
            found.update({row[0]: _row_to_reference(row) for row in rows})
        return found

    def elements_by_name(self, names: Sequence[str]) -> list[ElementRow]:
        """Alle Elemente mit einem dieser Namen und einer `id`, in Dokumentreihenfolge."""
        placeholders = ", ".join("?" * len(names))
        with self._lock:
            rows = self._db.execute(
                _ELEMENT_SELECT
                + f" WHERE e.name IN ({placeholders}) AND e.xml_id IS NOT NULL ORDER BY e.id",
                list(names),
            ).fetchall()
        return [_row_to_element(row) for row in rows]

    def frames(self, file_id: int | None = None) -> list[ElementRow]:
        """Alle Frames (optional einer Datei) in Dokumentreihenfolge."""
        condition = " WHERE e.is_frame = 1" + (" AND e.file_id = ?" if file_id is not None else "")
        params = () if file_id is None else (file_id,)
        with self._lock:
            rows = self._db.execute(
                _ELEMENT_SELECT + condition + " ORDER BY e.id", params
            ).fetchall()
        return [_row_to_element(row) for row in rows]

    def same_name_sibling_count(self, element: ElementRow) -> int:
        """Anzahl der Geschwister mit gleichem Namen (inklusive des Elements selbst)."""
        with self._lock:
            if element.parent_id is None:
                return 1
            row = self._db.execute(
                "SELECT COUNT(*) FROM elements WHERE parent_id = ? AND name = ?",
                (element.parent_id, element.name),
            ).fetchone()
        return int(row[0])

    def diagnostics(
        self, category: DiagnosticCategory | None = None, severity: Severity | None = None
    ) -> list[IndexedDiagnostic]:
        """Diagnosen, optional gefiltert nach Art und Schweregrad."""
        conditions: list[str] = []
        params: list[str] = []
        if category is not None:
            conditions.append("d.category = ?")
            params.append(category)
        if severity is not None:
            conditions.append("d.severity = ?")
            params.append(severity)
        where = (" WHERE " + " AND ".join(conditions)) if conditions else ""
        with self._lock:
            rows = self._db.execute(
                "SELECT d.file_id, f.name, d.category, d.severity, d.key, d.params, d.byte,"
                " d.char, d.line, d.column FROM diagnostics d JOIN files f ON f.id = d.file_id"
                + where
                + " ORDER BY d.file_id, d.id",
                params,
            ).fetchall()
        result = []
        for file_id, file_name, cat, sev, key, raw_params, byte, char, line, column in rows:
            position = None if byte is None else Position(byte, char, line, column)
            diagnostic = Diagnostic(
                DiagnosticCategory(cat),
                Severity(sev),
                MessageKey(key),
                json.loads(raw_params),
                position,
            )
            result.append(IndexedDiagnostic(file_id, file_name, diagnostic))
        return result
