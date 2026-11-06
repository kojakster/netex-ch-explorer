"""Commit-Datum aus dem `.git`-Ordner lesen, ohne Git-Programm (Entscheid „Commit-Datum“).

Gelesen werden lose Objekte (`objects/xx/…`) und Commits in Pack-Files (Index Version 2, SHA-1,
Pack-Offset unter 2 GB). Ein Commit, der als Delta gespeichert ist, ein SHA-256-Repository und alles
andere Ungewöhnliche ergeben `None`: Das Tool zeigt dann „Datum nicht ermittelbar“, nichts wird
geraten.

Sicherheit: Der Klon ist fremder Inhalt. Dateinamen entstehen nur aus der geprüften Commit-ID,
nichts wird ausgeführt, und es wird höchstens der Kopf eines Objekts entpackt (feste Obergrenze).
"""

from __future__ import annotations

import re
import struct
import zlib
from datetime import UTC, datetime, timedelta, timezone
from pathlib import Path
from typing import BinaryIO, Final

from app.core.guide.git import is_commit_id

_SHA1_HEX_LENGTH: Final = 40
_SHA1_LENGTH: Final = 20
_MAX_HEAD_BYTES: Final = 8192
"""Vom entpackten Commit wird höchstens so viel gelesen; der Kopf mit `committer` steht vorn."""
_MAX_COMPRESSED_BYTES: Final = 1_000_000
_MAX_PACK_COUNT: Final = 100
_IDX_MAGIC: Final = b"\xfftOc"
_IDX_VERSION: Final = 2
_FANOUT_ENTRIES: Final = 256
_OFFSET_64BIT_FLAG: Final = 0x80000000
_OBJ_COMMIT: Final = 1
_COMMITTER = re.compile(r"^committer .*> (\d{1,12}) ([+-])(\d{2})(\d{2})$")
_MAX_OFFSET_HOURS: Final = 14
_MAX_MINUTES: Final = 59


def read_commit_date(git_dir: Path, commit: str) -> str | None:
    """Datum des Commits (Committer) als ISO 8601 mit Zeitzone, z. B. `2026-11-04T09:16:10+01:00`.

    `None`, wenn das Objekt nicht gelesen werden kann (siehe Modulbeschreibung).
    """
    if len(commit) != _SHA1_HEX_LENGTH or not is_commit_id(commit):
        return None
    objects = _objects_dir(git_dir)
    try:
        head = _read_loose_head(objects, commit)
        if head is None:
            head = _read_packed_head(objects, commit)
    # Beschädigte oder unerwartete Dateien im fremden Klon sind keine Programmfehler.
    except (OSError, zlib.error, struct.error, ValueError, IndexError):
        return None
    return None if head is None else _committer_date(head)


def _objects_dir(git_dir: Path) -> Path:
    """Objektordner; bei Worktrees und Submodulen steht er im gemeinsamen Git-Ordner."""
    commondir_file = git_dir / "commondir"
    if commondir_file.is_file() and commondir_file.stat().st_size < _MAX_HEAD_BYTES:
        target = Path(commondir_file.read_text(encoding="utf-8").strip())
        return (target if target.is_absolute() else (git_dir / target).resolve()) / "objects"
    return git_dir / "objects"


def _read_loose_head(objects: Path, commit: str) -> bytes | None:
    path = objects / commit[:2] / commit[2:]
    if path.is_symlink() or not path.is_file() or path.stat().st_size > _MAX_COMPRESSED_BYTES:
        return None
    raw = zlib.decompressobj().decompress(path.read_bytes(), _MAX_HEAD_BYTES)
    header, separator, body = raw.partition(b"\0")
    if not separator or not header.startswith(b"commit "):
        return None
    return body


def _read_packed_head(objects: Path, commit: str) -> bytes | None:
    pack_dir = objects / "pack"
    if not pack_dir.is_dir():
        return None
    for index_path in sorted(pack_dir.glob("pack-*.idx"))[:_MAX_PACK_COUNT]:
        pack_path = index_path.with_suffix(".pack")
        if index_path.is_symlink() or pack_path.is_symlink() or not pack_path.is_file():
            continue
        with index_path.open("rb") as index_file:
            offset = _pack_offset(index_file, bytes.fromhex(commit))
        if offset is not None:
            return _read_pack_commit(pack_path, offset)
    return None


def _pack_offset(index: BinaryIO, sha: bytes) -> int | None:
    """Offset des Objekts im Pack (Index Version 2); `None`, wenn es nicht in diesem Pack liegt."""
    if index.read(4) != _IDX_MAGIC or struct.unpack(">I", index.read(4))[0] != _IDX_VERSION:
        return None
    fanout = struct.unpack(f">{_FANOUT_ENTRIES}I", index.read(4 * _FANOUT_ENTRIES))
    total = fanout[-1]
    low = fanout[sha[0] - 1] if sha[0] > 0 else 0
    high = fanout[sha[0]]
    names_start = 8 + 4 * _FANOUT_ENTRIES
    while low < high:
        middle = (low + high) // 2
        index.seek(names_start + middle * _SHA1_LENGTH)
        found = index.read(_SHA1_LENGTH)
        if found == sha:
            index.seek(names_start + total * (_SHA1_LENGTH + 4) + middle * 4)
            value: int = struct.unpack(">I", index.read(4))[0]
            return None if value & _OFFSET_64BIT_FLAG else value
        if found < sha:
            low = middle + 1
        else:
            high = middle
    return None


def _read_pack_commit(pack_path: Path, offset: int) -> bytes | None:
    """Kopf des Commits an `offset`; `None` bei anderen Objektarten (auch Delta)."""
    with pack_path.open("rb") as pack:
        pack.seek(offset)
        first = pack.read(1)[0]
        if (first >> 4) & 0b111 != _OBJ_COMMIT:
            return None
        while first & 0x80:  # Grössenangabe überspringen (wir brauchen sie nicht)
            first = pack.read(1)[0]
        return zlib.decompressobj().decompress(pack.read(_MAX_COMPRESSED_BYTES), _MAX_HEAD_BYTES)


def _committer_date(commit_body: bytes) -> str | None:
    """Liest Zeitstempel und Zeitzone aus der Zeile `committer` im Kopf des Commits."""
    header = commit_body.split(b"\n\n", 1)[0].decode("utf-8", errors="replace")
    for line in header.split("\n"):
        match = _COMMITTER.match(line)
        if match is None:
            continue
        seconds, sign, hours, minutes = match.groups()
        if int(hours) > _MAX_OFFSET_HOURS or int(minutes) > _MAX_MINUTES:
            return None
        offset = timedelta(hours=int(hours), minutes=int(minutes))
        zone = timezone(offset if sign == "+" else -offset)
        try:
            moment = datetime.fromtimestamp(int(seconds), UTC).astimezone(zone)
        except (OverflowError, OSError, ValueError):
            return None
        return moment.isoformat()
    return None
