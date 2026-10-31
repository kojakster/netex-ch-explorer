"""Eigene Dateien annehmen: Namen bereinigen, ZIP sicher entpacken, Ablage nur in `work/`.

Sicherheit (docs/engineering-guidelines.md): Dateinamen werden bereinigt, ZIP-Einträge dürfen den
Arbeitsordner nie verlassen (Zip-Slip), Symlinks werden abgewiesen, und die Grenzwerte aus
`config/settings.json` (`zipLimits`) gelten für Gesamtgrösse, Einzeldatei, Anzahl und
Kompressionsrate. Verarbeitet werden nur `.xml`-Einträge; der Rest wird als Hinweis gemeldet.
Fehler sind nie Abstürze, sondern Meldungen (`FileNote`) zu einer Datei. Die Gesamtgrenze gilt für
alle Dateien und alle ZIP-Archive eines Uploads zusammen.
"""

from __future__ import annotations

import logging
import re
import secrets
import shutil
import stat
import unicodedata
import zipfile
import zlib
from dataclasses import dataclass, field
from pathlib import Path, PurePosixPath
from typing import Final

from app.core.config import ZipLimits
from app.core.dataset import FileNote, SourceFile
from app.core.messages import MessageKey, ParamValue, Severity

logger = logging.getLogger(__name__)

WORK_DIR_NAME: Final = "work"
MAX_NAME_LENGTH: Final = 150
MAX_ENTRY_DEPTH: Final = 8
# Kleine Dateien komprimieren legitim sehr stark; die Rate zählt erst ab dieser Grösse.
MIN_RATIO_CHECK_BYTES: Final = 1024 * 1024
_CHUNK_BYTES: Final = 64 * 1024
_SESSION_TOKEN_BYTES: Final = 16
_SESSION_NAME = re.compile(r"^[A-Za-z0-9_-]{16,64}$")
_UNSAFE_CHARACTERS = re.compile(r"[^\w.\- ()+,@=]")
_WINDOWS_DEVICES: Final = frozenset(
    {"CON", "PRN", "AUX", "NUL"}
    | {f"COM{number}" for number in range(1, 10)}
    | {f"LPT{number}" for number in range(1, 10)}
)
# Windows behandelt auch hochgestellte Ziffern (COM¹) als Gerätenummer.
_SUPERSCRIPT_DIGITS: Final = str.maketrans("¹²³", "123")
_SKIPPED_EXAMPLES: Final = 5
_ZIP_ERRORS: Final = (zipfile.BadZipFile, RuntimeError, NotImplementedError, zlib.error, EOFError)


@dataclass(frozen=True)
class Upload:
    """Eine hochgeladene Datei: Name laut Browser (unzuverlässig) und Inhalt."""

    name: str
    data: bytes


@dataclass
class IntakeResult:
    """Die einlesbaren XML-Dateien und die Meldungen zu allem, was abgewiesen wurde."""

    sources: list[SourceFile] = field(default_factory=list)
    notes: list[FileNote] = field(default_factory=list)


class _ArchiveRejectedError(Exception):
    """Das ganze Archiv wird abgewiesen (Meldung ist bereits eingetragen)."""


def clean_name(raw: str) -> str:
    """Bereinigter Dateiname: ohne Ordner, nur sichere Zeichen, nie leer, nie ein Gerätename."""
    name = unicodedata.normalize("NFC", raw.replace("\\", "/").rsplit("/", 1)[-1])
    name = _UNSAFE_CHARACTERS.sub("_", name).strip(" .")[:MAX_NAME_LENGTH].strip(" .")
    if not name:
        return "datei"
    if _is_device_name(name):
        return f"_{name}"
    return name


def _is_device_name(name: str) -> bool:
    """Windows-Gerätename, auch mit Erweiterung, Leerzeichen vor dem Punkt oder `COM¹`."""
    base = name.split(".", 1)[0].rstrip(" .")
    return base.upper().translate(_SUPERSCRIPT_DIGITS) in _WINDOWS_DEVICES


class _Budget:
    """Gesamtgrenze in Bytes für alle entpackten und gespeicherten Dateien eines Uploads."""

    def __init__(self, limits: ZipLimits) -> None:
        self.limits = limits
        self.limit = limits.max_total_bytes
        self.used = 0

    @property
    def remaining(self) -> int:
        return max(self.limit - self.used, 0)


def _unique(name: str, used: set[str]) -> str:
    candidate = name
    stem, dot, suffix = name.rpartition(".")
    if not dot:
        stem, suffix = name, ""
    counter = 1
    while candidate.casefold() in used:
        counter += 1
        candidate = f"{stem}_{counter}{dot}{suffix}"
    used.add(candidate.casefold())
    return candidate


def _is_symlink(info: zipfile.ZipInfo) -> bool:
    mode = info.external_attr >> 16
    return stat.S_ISLNK(mode)


def _safe_parts(entry_name: str) -> list[str] | None:
    """Bereinigte Pfadteile eines Eintrags; `None`, wenn der Pfad unzulässig ist."""
    if "\x00" in entry_name or entry_name.startswith(("/", "\\")):
        return None
    normalized = entry_name.replace("\\", "/")
    path = PurePosixPath(normalized)
    parts = list(path.parts)
    if not parts or len(parts) > MAX_ENTRY_DEPTH:
        return None
    if any(part in {"..", "."} or ":" in part for part in parts):
        return None
    return [clean_name(part) for part in parts]


def _is_noise(entry_name: str) -> bool:
    """Betriebssystem-Beiwerk in ZIP-Dateien (macOS), das kein Fahrplan ist."""
    parts = PurePosixPath(entry_name.replace("\\", "/")).parts
    return parts[0] == "__MACOSX" or parts[-1].startswith("._")


class Workspace:
    """Arbeitsverzeichnis `work/`: je geöffnetem Datensatz ein Unterordner mit zufälligem Namen."""

    def __init__(self, root: Path) -> None:
        self.root = root

    def clear(self) -> None:
        """Löscht Reste früherer Läufe (nur Unterordner mit unseren Namen; folgt keinen Links)."""
        if self.root.is_symlink() or not self.root.is_dir():
            return
        for child in self.root.iterdir():
            if _SESSION_NAME.match(child.name):
                self._remove(child)

    def new_session(self) -> Path:
        """Legt den Ordner für einen Datensatz an."""
        self.root.mkdir(parents=True, exist_ok=True)
        session = self.root / secrets.token_urlsafe(_SESSION_TOKEN_BYTES)
        session.mkdir()
        return session

    def remove_session(self, session: Path) -> None:
        """Löscht den Ordner eines Datensatzes, sofern er in `work/` liegt."""
        if session.parent == self.root and _SESSION_NAME.match(session.name):
            self._remove(session)

    @staticmethod
    def _remove(path: Path) -> None:
        if path.is_symlink() or path.is_file():
            path.unlink(missing_ok=True)
        else:
            shutil.rmtree(path, ignore_errors=True)


def receive(uploads: list[Upload], session: Path, limits: ZipLimits) -> IntakeResult:
    """Nimmt die Dateien an: XML direkt, ZIP entpackt; alles landet nur im Ordner `session`."""
    result = IntakeResult()
    used_names: set[str] = set()
    budget = _Budget(limits)
    for number, upload in enumerate(uploads, start=1):
        name = clean_name(upload.name)
        lowered = name.lower()
        if lowered.endswith(".zip"):
            _note_name_change(result.notes, name, upload.name)
            zip_root = session / f"zip{number}"
            extractor = _ZipExtractor(name, zip_root / "entries", limits, used_names, budget)
            _receive_zip(upload, extractor, zip_root / "archive.zip")
            result.sources.extend(extractor.sources)
            result.notes.extend(extractor.notes)
        elif lowered.endswith(".xml"):
            unique = _unique(name, used_names)
            _note_name_change(result.notes, unique, upload.name)
            _receive_xml(upload, unique, session, budget, result)
        else:
            _note_name_change(result.notes, name, upload.name)
            result.notes.append(FileNote(name, Severity.ERROR, MessageKey.FILE_TYPE_UNSUPPORTED))
    return result


def _note_name_change(notes: list[FileNote], final_name: str, original: str) -> None:
    """Hinweis, wenn der Name vom hochgeladenen abweicht (bereinigt oder eindeutig gemacht)."""
    if final_name != original:
        notes.append(
            FileNote(
                final_name,
                Severity.INFO,
                MessageKey.FILE_NAME_CHANGED,
                {"original": original[:200]},
            )
        )


def _receive_xml(
    upload: Upload, name: str, session: Path, budget: _Budget, result: IntakeResult
) -> None:
    limits = budget.limits
    if not upload.data:
        result.notes.append(FileNote(name, Severity.ERROR, MessageKey.FILE_EMPTY))
        return
    if len(upload.data) > limits.max_file_bytes:
        result.notes.append(
            FileNote(
                name, Severity.ERROR, MessageKey.FILE_TOO_LARGE, {"limit": limits.max_file_bytes}
            )
        )
        return
    if len(upload.data) > budget.remaining:
        result.notes.append(
            FileNote(name, Severity.ERROR, MessageKey.FILE_TOTAL_TOO_LARGE, {"limit": budget.limit})
        )
        return
    target = session / "files" / name
    if not _store(target, upload.data):
        result.notes.append(FileNote(name, Severity.ERROR, MessageKey.FILE_WRITE_FAILED))
        return
    budget.used += len(upload.data)
    # Die Rohdaten liegen jetzt in work/; der Datensatz liest sie von dort.
    result.sources.append(SourceFile(name, upload.data, target))


def _store(target: Path, data: bytes) -> bool:
    """Schreibt die Datei in `work/`; `False` bei Schreibfehler."""
    try:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(data)
    except OSError:
        logger.exception("Datei konnte nicht in work/ gespeichert werden")
        return False
    return True


def _receive_zip(upload: Upload, extractor: _ZipExtractor, archive_path: Path) -> None:
    if not _store(archive_path, upload.data):
        extractor.error(MessageKey.FILE_WRITE_FAILED)
    else:
        try:
            with zipfile.ZipFile(archive_path) as archive:
                extractor.run(archive)
        except _ArchiveRejectedError:
            extractor.sources.clear()
        except (*_ZIP_ERRORS, OSError):
            extractor.error(MessageKey.ZIP_UNREADABLE)
            extractor.sources.clear()
    if extractor.skipped:
        extractor.info(
            MessageKey.ZIP_ENTRIES_SKIPPED,
            {
                "count": len(extractor.skipped),
                "examples": ", ".join(extractor.skipped[:_SKIPPED_EXAMPLES]),
            },
        )
    if not extractor.sources and not any(n.severity is Severity.ERROR for n in extractor.notes):
        extractor.notes.append(FileNote(extractor.name, Severity.WARNING, MessageKey.ZIP_NO_XML))


class _ZipExtractor:
    """Entpackt ein Archiv Eintrag für Eintrag in `work/` und sammelt Quellen und Meldungen."""

    def __init__(
        self,
        name: str,
        entries_root: Path,
        limits: ZipLimits,
        used_names: set[str],
        budget: _Budget,
    ) -> None:
        self.name = name
        self.entries_root = entries_root
        self.limits = limits
        self.used_names = used_names
        self.budget = budget
        self.sources: list[SourceFile] = []
        self.notes: list[FileNote] = []
        self.skipped: list[str] = []

    def error(self, key: MessageKey, params: dict[str, ParamValue] | None = None) -> None:
        """Trägt eine Fehlermeldung zum Archiv ein."""
        self.notes.append(FileNote(self.name, Severity.ERROR, key, params or {}))

    def info(self, key: MessageKey, params: dict[str, ParamValue] | None = None) -> None:
        """Trägt einen Hinweis zum Archiv ein."""
        self.notes.append(FileNote(self.name, Severity.INFO, key, params or {}))

    def run(self, archive: zipfile.ZipFile) -> None:
        """Prüft die Grenzwerte des ganzen Archivs und entpackt dann die XML-Einträge."""
        infos = archive.infolist()
        if len(infos) > self.limits.max_files:
            self.error(
                MessageKey.ZIP_TOO_MANY_FILES,
                {"count": len(infos), "limit": self.limits.max_files},
            )
            raise _ArchiveRejectedError
        if sum(info.file_size for info in infos) > self.budget.remaining:
            self.error(MessageKey.ZIP_TOTAL_TOO_LARGE, {"limit": self.limits.max_total_bytes})
            raise _ArchiveRejectedError
        for info in infos:
            if not info.is_dir():
                self._entry(archive, info)

    def _entry(self, archive: zipfile.ZipFile, info: zipfile.ZipInfo) -> None:
        shown = info.filename[:200]
        parts = _safe_parts(info.filename)
        if parts is None:
            self.error(MessageKey.ZIP_UNSAFE_PATH, {"entry": shown})
        elif _is_symlink(info):
            self.error(MessageKey.ZIP_SYMLINK, {"entry": shown})
        elif _is_noise(info.filename) or not parts[-1].lower().endswith(".xml"):
            self.skipped.append(shown)
        elif self._within_limits(info, shown):
            self._extract(archive, info, parts, shown)

    def _within_limits(self, info: zipfile.ZipInfo, shown: str) -> bool:
        if info.file_size > self.limits.max_file_bytes:
            self.error(
                MessageKey.ZIP_ENTRY_TOO_LARGE,
                {"entry": shown, "limit": self.limits.max_file_bytes},
            )
            return False
        if info.file_size >= MIN_RATIO_CHECK_BYTES:
            ratio = info.file_size // max(info.compress_size, 1)
            if ratio > self.limits.max_compression_ratio:
                self.error(
                    MessageKey.ZIP_COMPRESSION_RATIO,
                    {"entry": shown, "ratio": ratio, "limit": self.limits.max_compression_ratio},
                )
                return False
        return True

    def _extract(
        self, archive: zipfile.ZipFile, info: zipfile.ZipInfo, parts: list[str], shown: str
    ) -> None:
        display = _unique("/".join(parts), self.used_names)
        root = self.entries_root.resolve()
        target = root.joinpath(*display.split("/")).resolve()
        if not target.is_relative_to(root):
            self.error(MessageKey.ZIP_UNSAFE_PATH, {"entry": shown})
            return
        try:
            written = self._write_limited(archive, info, target)
            data = target.read_bytes()
        except _TotalExceededError:
            target.unlink(missing_ok=True)
            self.error(MessageKey.ZIP_TOTAL_TOO_LARGE, {"limit": self.limits.max_total_bytes})
            raise _ArchiveRejectedError from None
        except _LimitExceededError:
            self.error(
                MessageKey.ZIP_ENTRY_TOO_LARGE,
                {"entry": shown, "limit": self.limits.max_file_bytes},
            )
            target.unlink(missing_ok=True)
            return
        except (*_ZIP_ERRORS, OSError):
            self.error(MessageKey.ZIP_ENTRY_UNREADABLE, {"entry": shown})
            target.unlink(missing_ok=True)
            return
        self.budget.used += written
        _note_name_change(self.notes, display, info.filename)
        if not data:
            self.notes.append(FileNote(display, Severity.ERROR, MessageKey.FILE_EMPTY))
            return
        self.sources.append(SourceFile(display, data, target))

    def _write_limited(self, archive: zipfile.ZipFile, info: zipfile.ZipInfo, target: Path) -> int:
        """Schreibt den Eintrag; bricht ab, wenn mehr Bytes entstehen als erlaubt (Zip-Bombe)."""
        target.parent.mkdir(parents=True, exist_ok=True)
        remaining = self.budget.remaining
        allowed = min(self.limits.max_file_bytes, remaining)
        written = 0
        with archive.open(info) as source, target.open("xb") as destination:
            while chunk := source.read(_CHUNK_BYTES):
                written += len(chunk)
                if written > allowed:
                    raise (
                        _TotalExceededError
                        if allowed < self.limits.max_file_bytes
                        else _LimitExceededError
                    )
                destination.write(chunk)
        return written


class _LimitExceededError(Exception):
    """Ein Eintrag ist entpackt grösser als erlaubt."""


class _TotalExceededError(Exception):
    """Alle Einträge zusammen wären entpackt grösser als erlaubt."""
