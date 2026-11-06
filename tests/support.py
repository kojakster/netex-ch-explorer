"""Konstanten für die Tests."""

from __future__ import annotations

import hashlib
import zlib
from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

from app.core.config import load_config
from app.core.index.dataset_index import DatasetIndex, ElementRow

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = PROJECT_ROOT / "fixtures"
LOCALES_DIR = PROJECT_ROOT / "app" / "frontend" / "src" / "locales"
REQUIRE_GUIDE_ENV = "NETEX_REQUIRE_GUIDE"
# Die Zieltyp-Liste der Anwendung (config/ref-targets.json): Tests prüfen so das echte Verhalten.
REF_TARGETS = load_config(PROJECT_ROOT).ref_targets

SHA_A = "a" * 40
SHA_B = "b" * 40

type GitRepoFactory = Callable[..., Path]
type WorkbookFactory = Callable[[Path, Mapping[str, Sequence[Sequence[object]]]], Path]


def objects_by_id(index: DatasetIndex, xml_id: str, object_type: str) -> list[ElementRow]:
    """Objekte mit dieser `id` und diesem Typ (Elementname), in Dokumentreihenfolge."""
    return [row for row in index.elements_by_name([object_type]) if row.xml_id == xml_id]


COMMIT_TEXT = (
    "tree 4b825dc642cb6eb9a060e54bf8d69288fbee4904\n"
    "author A <a@example.org> 1793780170 +0100\n"
    "committer Synthetisch <s@example.org> 1793780170 +0100\n"
    "\nSynthetischer Commit\n"
)
EXPECTED_DATE = "2026-11-04T09:16:10+01:00"


def commit_object(text: str = COMMIT_TEXT) -> tuple[str, bytes]:
    """Commit-ID und Inhalt eines Commits (`commit <Länge>\\0…`)."""
    body = text.encode()
    raw = b"commit " + str(len(body)).encode() + b"\0" + body
    return hashlib.sha1(raw, usedforsecurity=False).hexdigest(), raw


def write_loose(git_dir: Path, text: str = COMMIT_TEXT) -> str:
    sha, raw = commit_object(text)
    path = git_dir / "objects" / sha[:2] / sha[2:]
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(zlib.compress(raw))
    return sha
