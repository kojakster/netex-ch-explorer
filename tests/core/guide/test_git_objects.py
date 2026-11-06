"""Commit-Datum aus synthetischen Git-Objekten (lose und im Pack), ohne Git-Programm."""

from __future__ import annotations

import hashlib
import struct
import zlib
from pathlib import Path

import pytest

from app.core.guide.git_objects import read_commit_date
from tests.support import COMMIT_TEXT, EXPECTED_DATE, SHA_A, commit_object, write_loose

OBJ_COMMIT = 1
OBJ_BLOB = 3
OBJ_OFS_DELTA = 6


def pack_header(object_type: int, size: int) -> bytes:
    """Objektkopf im Pack: Typ und Grösse als Varint."""
    first = (object_type << 4) | (size & 0x0F)
    size >>= 4
    out = bytearray()
    while size:
        out.append(first | 0x80)
        first = size & 0x7F
        size >>= 7
    out.append(first)
    return bytes(out)


def write_pack(
    git_dir: Path,
    entries: list[tuple[str, int, bytes]],
    *,
    name: str = "pack-0001",
    big_offset_flag: bool = False,
) -> None:
    """Schreibt Pack und Index (Version 2). Einträge: (SHA, Typ, entpackter Inhalt)."""
    pack = bytearray(b"PACK" + struct.pack(">II", 2, len(entries)))
    offsets: dict[str, int] = {}
    for sha, object_type, content in entries:
        offsets[sha] = len(pack)
        pack += pack_header(object_type, len(content)) + zlib.compress(content)
    pack += hashlib.sha1(bytes(pack), usedforsecurity=False).digest()
    shas = sorted(offsets)
    counts = [sum(1 for sha in shas if int(sha[:2], 16) <= i) for i in range(256)]
    index = bytearray(b"\xfftOc" + struct.pack(">I", 2) + struct.pack(">256I", *counts))
    index += b"".join(bytes.fromhex(sha) for sha in shas)
    index += b"\0\0\0\0" * len(shas)  # CRC32, wird nicht gelesen
    for sha in shas:
        value = offsets[sha] | (0x80000000 if big_offset_flag else 0)
        index += struct.pack(">I", value)
    index += hashlib.sha1(bytes(pack[-20:]), usedforsecurity=False).digest() * 2
    pack_dir = git_dir / "objects" / "pack"
    pack_dir.mkdir(parents=True, exist_ok=True)
    (pack_dir / f"{name}.pack").write_bytes(bytes(pack))
    (pack_dir / f"{name}.idx").write_bytes(bytes(index))


@pytest.fixture
def git_dir(tmp_path: Path) -> Path:
    path = tmp_path / ".git"
    path.mkdir()
    return path


def test_loose_commit(git_dir: Path) -> None:
    sha = write_loose(git_dir)
    assert read_commit_date(git_dir, sha) == EXPECTED_DATE


def test_commit_in_pack(git_dir: Path) -> None:
    sha, raw = commit_object()
    other = "ab" + "0" * 38
    write_pack(
        git_dir,
        [(other, OBJ_BLOB, b"blob"), (sha, OBJ_COMMIT, raw.partition(b"\0")[2])],
    )
    assert read_commit_date(git_dir, sha) == EXPECTED_DATE


def test_commit_in_the_second_pack(git_dir: Path) -> None:
    sha, raw = commit_object()
    write_pack(git_dir, [("ab" + "0" * 38, OBJ_BLOB, b"x")], name="pack-0001")
    write_pack(git_dir, [(sha, OBJ_COMMIT, raw.partition(b"\0")[2])], name="pack-0002")
    assert read_commit_date(git_dir, sha) == EXPECTED_DATE


def test_commit_with_long_header_size(git_dir: Path) -> None:
    text = COMMIT_TEXT + "x" * 5000
    sha, raw = commit_object(text)
    write_pack(git_dir, [(sha, OBJ_COMMIT, raw.partition(b"\0")[2])])
    assert read_commit_date(git_dir, sha) == EXPECTED_DATE


def test_negative_and_utc_offsets(git_dir: Path) -> None:
    negative = COMMIT_TEXT.replace("1793780170 +0100\n\n", "1793780170 -0530\n\n")
    assert read_commit_date(git_dir, write_loose(git_dir, negative)) == "2026-11-04T02:46:10-05:30"
    utc = COMMIT_TEXT.replace("1793780170 +0100\n\n", "1793780170 +0000\n\n")
    assert read_commit_date(git_dir, write_loose(git_dir, utc)) == "2026-11-04T08:16:10+00:00"


def test_delta_commit_is_not_read(git_dir: Path) -> None:
    sha, raw = commit_object()
    write_pack(git_dir, [(sha, OBJ_OFS_DELTA, raw.partition(b"\0")[2])])
    assert read_commit_date(git_dir, sha) is None


def test_object_of_another_type_is_not_a_commit(git_dir: Path) -> None:
    sha, raw = commit_object()
    write_pack(git_dir, [(sha, OBJ_BLOB, raw.partition(b"\0")[2])])
    assert read_commit_date(git_dir, sha) is None


def test_64bit_offsets_are_not_read(git_dir: Path) -> None:
    sha, raw = commit_object()
    write_pack(git_dir, [(sha, OBJ_COMMIT, raw.partition(b"\0")[2])], big_offset_flag=True)
    assert read_commit_date(git_dir, sha) is None


def test_missing_commit(git_dir: Path) -> None:
    assert read_commit_date(git_dir, SHA_A) is None
    write_pack(git_dir, [("ab" + "0" * 38, OBJ_BLOB, b"x")])
    assert read_commit_date(git_dir, SHA_A) is None
    assert read_commit_date(git_dir, "00" + "f" * 38) is None


@pytest.mark.parametrize("commit", ["", "xyz", "A" * 40, "a" * 64, "../" + "a" * 37])
def test_invalid_commit_ids(git_dir: Path, commit: str) -> None:
    assert read_commit_date(git_dir, commit) is None


@pytest.mark.parametrize(
    "text",
    [
        "tree x\n\nohne committer\n",
        "committer Name <n@e.org> abc +0100\n\nx\n",
        "committer Name <n@e.org> 1793780170 +9900\n\nx\n",
        "committer Name <n@e.org> 1793780170 +0199\n\nx\n",
        "committer Name <n@e.org> 999999999999 +0100\n\nx\n",
    ],
)
def test_unusable_committer_line(git_dir: Path, text: str) -> None:
    assert read_commit_date(git_dir, write_loose(git_dir, text)) is None


def test_damaged_files_give_none(git_dir: Path) -> None:
    sha = write_loose(git_dir)
    (git_dir / "objects" / sha[:2] / sha[2:]).write_bytes(b"kein zlib")
    assert read_commit_date(git_dir, sha) is None
    other = "cd" + "1" * 38
    path = git_dir / "objects" / other[:2] / other[2:]
    path.parent.mkdir(parents=True)
    path.write_bytes(zlib.compress(b"blob 3\0abc"))
    assert read_commit_date(git_dir, other) is None
    path.write_bytes(zlib.compress(b"ohne trennzeichen"))
    assert read_commit_date(git_dir, other) is None


def test_damaged_pack_files_give_none(git_dir: Path) -> None:
    sha, raw = commit_object()
    write_pack(git_dir, [(sha, OBJ_COMMIT, raw.partition(b"\0")[2])])
    pack_dir = git_dir / "objects" / "pack"
    (pack_dir / "pack-0001.pack").write_bytes(b"PACK")
    assert read_commit_date(git_dir, sha) is None
    (pack_dir / "pack-0001.idx").write_bytes(b"\xfftOc\0\0\0\3")
    assert read_commit_date(git_dir, sha) is None
    (pack_dir / "pack-0001.idx").write_bytes(b"kaputt!!")
    assert read_commit_date(git_dir, sha) is None


def test_index_without_matching_pack_is_skipped(git_dir: Path) -> None:
    sha, raw = commit_object()
    write_pack(git_dir, [(sha, OBJ_COMMIT, raw.partition(b"\0")[2])])
    (git_dir / "objects" / "pack" / "pack-0001.pack").unlink()
    assert read_commit_date(git_dir, sha) is None


def test_symbolic_links_are_not_followed(git_dir: Path, tmp_path: Path) -> None:
    sha, raw = commit_object()
    outside = tmp_path / "outside"
    outside.mkdir()
    (outside / "objekt").write_bytes(zlib.compress(raw))
    link = git_dir / "objects" / sha[:2] / sha[2:]
    link.parent.mkdir(parents=True)
    link.symlink_to(outside / "objekt")
    assert read_commit_date(git_dir, sha) is None


def test_decompression_is_bounded(git_dir: Path) -> None:
    """Ein riesiger entpackter Inhalt wird nur bis zur Obergrenze gelesen (Kopf genügt)."""
    text = COMMIT_TEXT + "y" * 5_000_000
    assert read_commit_date(git_dir, write_loose(git_dir, text)) == EXPECTED_DATE


def test_objects_of_a_worktree_come_from_the_common_dir(tmp_path: Path) -> None:
    common = tmp_path / "common"
    sha = write_loose(common)
    worktree = tmp_path / "worktree"
    worktree.mkdir()
    (worktree / "commondir").write_text("../common\n", encoding="utf-8")
    assert read_commit_date(worktree, sha) == EXPECTED_DATE
    absolute = tmp_path / "worktree2"
    absolute.mkdir()
    (absolute / "commondir").write_text(str(common), encoding="utf-8")
    assert read_commit_date(absolute, sha) == EXPECTED_DATE
