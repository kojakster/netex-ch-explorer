"""Datensatz: eine oder mehrere eingelesene Dateien mit gemeinsamem Index."""

from __future__ import annotations

import hashlib
import logging
import threading
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass, field
from pathlib import Path

from app.core.diagnostics import Diagnostic, DiagnosticCategory
from app.core.index.dataset_index import DatasetIndex
from app.core.messages import MessageKey, ParamValue, Severity
from app.core.reader.xml_reader import ParsedFile, read_xml
from app.core.validation.detection import VersionDetection, detect_version
from app.core.validation.result import ValidationSummary

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class SourceFile:
    """Eine Datei zum Öffnen: Anzeigename, Inhalt und Ablageort.

    Mit `path` (Datei in `work/` oder Beispiel des Guides) liest der Datensatz die Rohdaten für die
    Validierung bei Bedarf von dort. Ohne `path` (synthetische Daten) behält er sie im Speicher.
    """

    name: str
    data: bytes
    path: Path | None = None


@dataclass(frozen=True)
class FileNote:
    """Meldung zu einer Datei oder einem Archiv beim Öffnen; wird zur Diagnose der Art `file`."""

    file_name: str
    severity: Severity
    key: MessageKey
    params: Mapping[str, ParamValue] = field(default_factory=dict)


class Dataset:
    """Geöffneter Datensatz; schliessen gibt den Index frei und löscht die Dateien in `work/`.

    Anfragen, die den Datensatz benutzen, halten ihn mit `acquire` fest und geben ihn mit
    `release` wieder frei. `close` während einer Benutzung wirkt erst, wenn die letzte Anfrage
    fertig ist; so bricht das Schliessen (oder das Herausfallen aus der Liste offener Datensätze)
    keine laufende Anfrage ab.

    Attributes:
        index: Index aller Elemente.
        detections: Versionserkennung je Datei-ID.
        validation: Ergebnis der letzten Validierung, `None` vor der ersten.
        validation_lock: Serialisiert Validierungen desselben Datensatzes.
    """

    def __init__(
        self,
        index: DatasetIndex,
        raw_paths: dict[int, Path],
        raw_memory: dict[int, bytes],
        detections: dict[int, VersionDetection],
        release: Callable[[], None] | None = None,
    ) -> None:
        self.index = index
        self.detections = detections
        self.validation: ValidationSummary | None = None
        self.validation_lock = threading.Lock()
        self._raw_paths = raw_paths
        self._raw_memory = raw_memory
        self._release = release
        self._state_lock = threading.Lock()
        self._uses = 0
        self._closing = False
        self._closed = False

    def read_file(self, file_id: int) -> bytes | None:
        """Rohdaten einer Datei (für XSD und Schematron); `None`, wenn sie nicht vorliegen."""
        path = self._raw_paths.get(file_id)
        if path is None:
            return self._raw_memory.get(file_id)
        try:
            return path.read_bytes()
        except OSError:
            logger.exception("Datei %s konnte nicht gelesen werden", file_id)
            return None

    def acquire(self) -> bool:
        """Hält den Datensatz für eine Anfrage fest; `False`, wenn er schon geschlossen wird."""
        with self._state_lock:
            if self._closing:
                return False
            self._uses += 1
            return True

    def release(self) -> None:
        """Gibt eine Anfrage frei; die letzte Anfrage nach einem `close` schliesst wirklich."""
        with self._state_lock:
            self._uses -= 1
            finish = self._closing and self._uses == 0
        if finish:
            self._finish()

    def close(self) -> None:
        """Schliesst den Datensatz (löscht Dateien in `work/`, gibt den Index frei).

        Läuft noch eine Anfrage, geschieht das erst nach deren Ende. Mehrfaches Schliessen ist
        unschädlich.
        """
        with self._state_lock:
            self._closing = True
            finish = self._uses == 0
        if finish:
            self._finish()

    def _finish(self) -> None:
        with self._state_lock:
            if self._closed:
                return
            self._closed = True
            release, self._release = self._release, None
        if release is not None:
            release()
        self.index.close()


def _placeholder(name: str) -> ParsedFile:
    """Eintrag für eine Datei, die nicht eingelesen werden konnte (nur mit Meldungen)."""
    return ParsedFile(name=name, size=0, sha256=hashlib.sha256(b"").hexdigest(), text="")


def open_dataset(
    sources: Iterable[SourceFile],
    not_relevant: Iterable[str],
    ref_targets: Mapping[str, tuple[str, ...]],
    notes: Iterable[FileNote] = (),
    release: Callable[[], None] | None = None,
) -> Dataset:
    """Liest alle Dateien ein und baut den Index. Fehler werden zu Diagnosen.

    `notes` sind Meldungen des Öffnens (abgewiesene Dateien, ZIP-Probleme); zu Dateien, die nicht
    eingelesen wurden, entsteht ein Eintrag ohne Inhalt, damit die Meldung sichtbar bleibt.
    """
    source_list = list(sources)
    parsed = [read_xml(source.name, source.data) for source in source_list]
    numbered = list(enumerate(source_list, start=1))
    raw_paths = {number: source.path for number, source in numbered if source.path is not None}
    raw_memory = {number: source.data for number, source in numbered if source.path is None}
    by_name = {file.name: file for file in parsed}
    for note in notes:
        target = by_name.get(note.file_name)
        if target is None:
            target = _placeholder(note.file_name)
            by_name[note.file_name] = target
            parsed.append(target)
        target.diagnostics.append(
            Diagnostic(
                DiagnosticCategory.FILE, note.severity, note.key, dict(note.params), position=None
            )
        )
    detections = {number: detect_version(file) for number, file in enumerate(parsed, start=1)}
    index = DatasetIndex(parsed, not_relevant, ref_targets)
    return Dataset(index, raw_paths, raw_memory, detections, release)
