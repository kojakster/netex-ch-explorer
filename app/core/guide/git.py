"""Branch und Commit eines Git-Klons direkt aus dem `.git`-Ordner lesen, ohne Git-Programm.

Unterstützt werden ein `.git`-Ordner, eine `.git`-Datei mit `gitdir:` (Submodul, Worktree),
lose Referenzen, `packed-refs` und ein losgelöster HEAD. Das Commit-Datum liest
`git_objects.py` (docs/decisions.md, „Commit-Datum“).
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import Final

_SHA = re.compile(r"^(?:[0-9a-f]{40}|[0-9a-f]{64})$")
_GITDIR_PREFIX: Final = "gitdir:"
_SYMREF_PREFIX: Final = "ref:"
_MAX_SMALL_FILE_BYTES: Final = 4096
_MAX_PACKED_REFS_BYTES: Final = 10_000_000
_MAX_SYMREF_DEPTH: Final = 5


def is_commit_id(value: str) -> bool:
    """Prüft, ob `value` eine vollständige Commit-ID ist (SHA-1 oder SHA-256, Kleinbuchstaben)."""
    return _SHA.match(value) is not None


class GitReadError(Exception):
    """Der `.git`-Ordner ist nicht lesbar oder hat nicht das erwartete Format."""


@dataclass(frozen=True)
class GitHead:
    """Stand von HEAD.

    Attributes:
        branch: Name des Branches, `None` bei losgelöstem HEAD.
        commit: Vollständige Commit-ID, `None` wenn der Branch noch keinen Commit hat.
    """

    branch: str | None
    commit: str | None


def find_git_dir(work_tree: Path) -> Path | None:
    """Gibt den Git-Ordner des Arbeitsverzeichnisses zurück oder `None`, wenn es keiner ist.

    Raises:
        GitReadError: Die `.git`-Datei verweist auf keinen vorhandenen Ordner.
    """
    dot_git = work_tree / ".git"
    if dot_git.is_dir():
        return dot_git
    if not dot_git.is_file():
        return None
    content = _read_small_text(dot_git)
    if not content.startswith(_GITDIR_PREFIX):
        raise GitReadError(dot_git)
    target = Path(content.removeprefix(_GITDIR_PREFIX).strip())
    git_dir = target if target.is_absolute() else (work_tree / target).resolve()
    if not git_dir.is_dir():
        raise GitReadError(git_dir)
    return git_dir


def read_head(git_dir: Path) -> GitHead:
    """Liest Branch und Commit von HEAD.

    Raises:
        GitReadError: HEAD oder eine Referenz hat kein gültiges Format.
    """
    head = _read_small_text(git_dir / "HEAD")
    if _SHA.match(head):
        return GitHead(branch=None, commit=head)
    if not head.startswith(_SYMREF_PREFIX):
        raise GitReadError(git_dir / "HEAD")
    ref = head.removeprefix(_SYMREF_PREFIX).strip()
    branch = ref.removeprefix("refs/heads/") if ref.startswith("refs/heads/") else None
    return GitHead(branch=branch, commit=_resolve_ref(git_dir, ref, depth=0))


def _common_dir(git_dir: Path) -> Path:
    """Gibt den gemeinsamen Git-Ordner zurück (bei Worktrees über die Datei `commondir`)."""
    commondir_file = git_dir / "commondir"
    if not commondir_file.is_file():
        return git_dir
    target = Path(_read_small_text(commondir_file))
    return target if target.is_absolute() else (git_dir / target).resolve()


def _resolve_ref(git_dir: Path, ref: str, depth: int) -> str | None:
    if depth > _MAX_SYMREF_DEPTH:
        raise GitReadError(ref)
    ref_path = _checked_ref_path(ref)
    for base in dict.fromkeys((git_dir, _common_dir(git_dir))):
        loose = base.joinpath(*ref_path.parts)
        if loose.is_file():
            value = _read_small_text(loose)
            if value.startswith(_SYMREF_PREFIX):
                return _resolve_ref(git_dir, value.removeprefix(_SYMREF_PREFIX).strip(), depth + 1)
            if not _SHA.match(value):
                raise GitReadError(loose)
            return value
    return _lookup_packed_ref(_common_dir(git_dir), ref)


def _checked_ref_path(ref: str) -> PurePosixPath:
    """Prüft, dass eine Referenz unter `refs/` liegt und den Git-Ordner nicht verlässt."""
    path = PurePosixPath(ref)
    if path.is_absolute() or not ref.startswith("refs/") or ".." in path.parts:
        raise GitReadError(ref)
    return path


def _lookup_packed_ref(git_dir: Path, ref: str) -> str | None:
    packed = git_dir / "packed-refs"
    if not packed.is_file():
        return None
    try:
        if packed.stat().st_size > _MAX_PACKED_REFS_BYTES:
            raise GitReadError(packed)
        lines = packed.read_text(encoding="utf-8").splitlines()
    except (OSError, UnicodeDecodeError) as error:
        raise GitReadError(packed) from error
    for line in lines:
        if not line or line.startswith(("#", "^")):
            continue
        sha, _, name = line.partition(" ")
        if name == ref:
            if not _SHA.match(sha):
                raise GitReadError(packed)
            return sha
    return None


def _read_small_text(path: Path) -> str:
    try:
        if path.stat().st_size > _MAX_SMALL_FILE_BYTES:
            raise GitReadError(path)
        return path.read_text(encoding="utf-8").strip()
    except (OSError, UnicodeDecodeError) as error:
        raise GitReadError(path) from error
