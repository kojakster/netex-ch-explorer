"""Gemeinsame Hilfen der Skripte für die Oberfläche (`app/frontend`)."""

from __future__ import annotations

from pathlib import Path
from typing import Final

PROJECT_ROOT: Final = Path(__file__).resolve().parent.parent
FRONTEND_DIR: Final = PROJECT_ROOT / "app" / "frontend"
# Was die gebaute Oberfläche beeinflusst; ist etwas davon neuer als der Build, wird neu gebaut.
FRONTEND_SOURCES: Final = (
    "src",
    "public",
    "index.html",
    "package.json",
    "package-lock.json",
    "vite.config.ts",
    "tsconfig.json",
)


def _newest_mtime(paths: list[Path]) -> float:
    newest = 0.0
    for path in paths:
        if path.is_file():
            newest = max(newest, path.stat().st_mtime)
        elif path.is_dir():
            newest = max(
                [newest, *(item.stat().st_mtime for item in path.rglob("*") if item.is_file())]
            )
    return newest


def frontend_needs_build(frontend_dir: Path) -> bool:
    """Prüft, ob der Build fehlt oder älter als eine Quelldatei ist."""
    built = frontend_dir / "dist" / "index.html"
    if not built.is_file():
        return True
    sources = [frontend_dir / name for name in FRONTEND_SOURCES]
    return _newest_mtime(sources) > built.stat().st_mtime


def dependencies_need_install(frontend_dir: Path) -> bool:
    """Prüft, ob `node_modules` fehlt oder älter als `package-lock.json` ist."""
    marker = frontend_dir / "node_modules" / ".package-lock.json"
    lock = frontend_dir / "package-lock.json"
    return not marker.is_file() or lock.stat().st_mtime > marker.stat().st_mtime
