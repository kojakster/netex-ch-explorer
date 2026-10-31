"""Verweise auf Guide-Kapitel über `src/A5_annex_index.md`.

Der Index nennt zu jedem Elementnamen die Kapitel, in denen er vorkommt. Das Tool verlinkt das
erste Kapitel der Liste (Kapitel `NN_…` und `ucNN_…`; Tabellenseiten, Anhänge und `index` zählen
nicht) und zwar auf GitHub im **exakt verwendeten Commit**, nicht auf die veröffentlichte Seite,
die einen anderen Stand zeigen kann (docs/decisions.md, „Validierung mit Erklärung“).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

from app.core.guide.git import is_commit_id
from app.core.guide.layout import ANNEX_INDEX_FILE, GUIDE_REPOSITORY_URL

_ENTRY = re.compile(r"^- ([A-Za-z0-9_.]+): (.+)$")
_CHAPTER = re.compile(r"\]\(((?:uc)?\d{2}_[A-Za-z0-9_]+)\.html(?:#[^)]*)?\)")
_MAX_INDEX_BYTES: Final = 2_000_000


@dataclass(frozen=True)
class GuideLinks:
    """Kapitel je Elementname (relative Pfade im Guide-Klon, z. B. `src/08_timetable.md`)."""

    chapters: dict[str, str] = field(default_factory=dict)

    def chapter(self, element: str | None) -> str | None:
        """Relativer Pfad des Kapitels zum Element; `None`, wenn der Index es nicht nennt."""
        return None if element is None else self.chapters.get(element)


def read_guide_links(guide_path: Path) -> GuideLinks:
    """Liest den Index des Guides; fehlt er oder ist er unlesbar, gibt es keine Verweise."""
    path = guide_path.joinpath(*ANNEX_INDEX_FILE.parts)
    try:
        if not path.is_file() or path.stat().st_size > _MAX_INDEX_BYTES:
            return GuideLinks()
        text = path.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return GuideLinks()
    chapters: dict[str, str] = {}
    for line in text.splitlines():
        entry = _ENTRY.match(line)
        if entry is None:
            continue
        chapter = _CHAPTER.search(entry.group(2))
        if chapter is not None:
            chapters[entry.group(1)] = f"{ANNEX_INDEX_FILE.parent}/{chapter.group(1)}.md"
    return GuideLinks(chapters)


def guide_url(commit: str | None, relative_path: str | None) -> str | None:
    """GitHub-Adresse der Datei im Commit; `None` ohne gültigen Commit oder Pfad."""
    if commit is None or relative_path is None or not is_commit_id(commit):
        return None
    return f"{GUIDE_REPOSITORY_URL}/blob/{commit}/{relative_path}"
