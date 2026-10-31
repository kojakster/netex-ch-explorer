"""Datensatz: eine oder mehrere eingelesene Dateien mit gemeinsamem Index."""

from __future__ import annotations

import hashlib
import threading
from collections.abc import Callable, Iterable, Mapping
from dataclasses import dataclass

from app.core.diagnostics import Diagnostic, DiagnosticCategory
from app.core.index.dataset_index import DatasetIndex
from app.core.messages import MessageKey, ParamValue, Severity
from app.core.reader.xml_reader import ParsedFile, read_xml
from app.core.validation.detection import VersionDetection, detect_version
from app.core.validation.result import ValidationSummary


@dataclass(frozen=True)
class SourceFile:
    """Eine Datei zum Öffnen: Anzeigename und Inhalt."""

    name: str
    data: bytes


@dataclass(frozen=True)
class FileNote:
    """Meldung zu einer Datei beim Öffnen (z. B. abgewiesener Upload); wird zur Diagnose `file`."""

    file_name: str
    severity: Severity
    key: MessageKey
    params: Mapping[str, ParamValue]


class Dataset:
    """Geöffneter Datensatz; schliessen gibt den Index frei und löscht die Dateien in `work/`.

    Attributes:
        index: Index aller Elemente.
        file_data: Inhalt der lesbaren Dateien, nach Datei-ID im Index (für XSD und Schematron).
        detections: Versionserkennung je Datei-ID.
        validation: Ergebnis der letzten Validierung, `None` vor der ersten.
        validation_lock: Serialisiert Validierungen desselben Datensatzes.
    """

    def __init__(
        self,
        index: DatasetIndex,
        file_data: dict[int, bytes],
        detections: dict[int, VersionDetection],
        release: Callable[[], None] | None = None,
    ) -> None:
        self.index = index
        self.file_data = file_data
        self.detections = detections
        self.validation: ValidationSummary | None = None
        self.validation_lock = threading.Lock()
        self._release = release

    def release_files(self) -> None:
        """Löscht die Dateien in `work/` (einmalig); der Index bleibt benutzbar."""
        release, self._release = self._release, None
        if release is not None:
            release()

    def close(self) -> None:
        """Löscht die Dateien in `work/` und gibt den Index frei."""
        self.release_files()
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
    file_data = {number: source.data for number, source in enumerate(source_list, start=1)}
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
    return Dataset(DatasetIndex(parsed, not_relevant, ref_targets), file_data, detections, release)
