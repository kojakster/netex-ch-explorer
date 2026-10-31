"""Prüfbefehl: führt alle Qualitätsprüfungen aus und muss vor jedem Commit grün sein.

Reihenfolge: Lockfile, ruff (Prüfung und Formatierung), mypy --strict, pytest mit Abdeckung
≥ 90 % für `app/core` (inklusive Schichten- und Hilfeseiten-Test), Frontend (Typprüfung,
Biome, Vitest, Build), pip-audit, npm audit, Git-Hook aktiv. Alle Schritte laufen auch nach
einem Fehler weiter; am Ende steht eine Zusammenfassung. Aufruf: `uv run python scripts/check.py`.
Die Sicherheitsprüfungen der Abhängigkeiten brauchen eine Internetverbindung. Mit `--hook`
(Git-Hook) wird zuerst geprüft, dass das Arbeitsverzeichnis dem Commit-Inhalt entspricht.
"""

from __future__ import annotations

import argparse
import logging
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from frontend import FRONTEND_DIR, PROJECT_ROOT, dependencies_need_install

CORE_COVERAGE_MINIMUM: Final = 90
HOOKS_PATH: Final = ".githooks"

logger = logging.getLogger("check")


@dataclass(frozen=True)
class Step:
    """Ein Prüfschritt: Name und Funktion, die `True` bei Erfolg liefert."""

    name: str
    run: Callable[[], bool]


def _tool(name: str) -> str:
    path = shutil.which(name)
    if path is None:
        message = f"Programm nicht gefunden: {name}"
        raise FileNotFoundError(message)
    return path


def _run(command: list[str], cwd: Path = PROJECT_ROOT) -> bool:
    return subprocess.run(command, cwd=cwd, check=False).returncode == 0


def _python(*args: str) -> Callable[[], bool]:
    return lambda: _run([sys.executable, "-m", *args])


def _npm(*args: str) -> Callable[[], bool]:
    return lambda: _run([_tool("npm"), *args], cwd=FRONTEND_DIR)


def _ensure_frontend_packages() -> bool:
    if not dependencies_need_install(FRONTEND_DIR):
        return True
    return _run([_tool("npm"), "ci"], cwd=FRONTEND_DIR)


def _index_matches_worktree() -> bool:
    """Im Git-Hook: Geprüft wird das Arbeitsverzeichnis; es muss dem Commit-Inhalt entsprechen."""
    git = _tool("git")
    unstaged = subprocess.run([git, "diff", "--quiet"], cwd=PROJECT_ROOT, check=False)
    untracked = subprocess.run(
        [git, "ls-files", "--others", "--exclude-standard"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if unstaged.returncode == 0 and not untracked.stdout.strip():
        return True
    logger.error(
        "Nicht vorgemerkte Änderungen oder neue Dateien: Der Prüfbefehl prüft das "
        "Arbeitsverzeichnis, nicht den Commit-Inhalt. Erst alles vormerken (git add) oder "
        "beiseitelegen (git stash --keep-index --include-untracked)."
    )
    return False


def _lock_is_current() -> bool:
    return _run([_tool("uv"), "lock", "--check"])


def _pip_audit() -> bool:
    """Prüft die festgeschriebenen Python-Pakete (aus `uv.lock`) auf bekannte Sicherheitslücken."""
    with tempfile.TemporaryDirectory() as directory:
        requirements = Path(directory) / "requirements.txt"
        exported = _run(
            [
                _tool("uv"),
                "export",
                "--quiet",
                "--frozen",
                "--all-groups",
                "--no-emit-project",
                "--format",
                "requirements-txt",
                "--output-file",
                str(requirements),
            ]
        )
        if not exported:
            return False
        return _run(
            [
                sys.executable,
                "-m",
                "pip_audit",
                "--requirement",
                str(requirements),
                "--require-hashes",
                "--disable-pip",
                "--progress-spinner",
                "off",
            ]
        )


def _hook_active() -> bool:
    result = subprocess.run(
        [_tool("git"), "config", "--get", "core.hooksPath"],
        cwd=PROJECT_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if result.stdout.strip() == HOOKS_PATH:
        return True
    logger.error(
        "Git-Hook nicht aktiv. Einmalig ausführen: git config core.hooksPath %s", HOOKS_PATH
    )
    return False


STEPS: Final = (
    Step("uv.lock aktuell", _lock_is_current),
    Step("ruff check", _python("ruff", "check", ".")),
    Step("ruff format", _python("ruff", "format", "--check", ".")),
    Step("mypy --strict", _python("mypy")),
    Step(
        "pytest + Abdeckung app/core",
        _python(
            "pytest",
            "--cov=app/core",
            "--cov-report=term",
            f"--cov-fail-under={CORE_COVERAGE_MINIMUM}",
        ),
    ),
    Step("npm ci (falls nötig)", _ensure_frontend_packages),
    Step("Frontend: TypeScript", _npm("run", "typecheck")),
    Step("Frontend: Biome", _npm("run", "lint")),
    Step("Frontend: Vitest", _npm("run", "test")),
    Step("Frontend: Build", _npm("run", "build")),
    Step("pip-audit", _pip_audit),
    Step("npm audit", _npm("audit", "--audit-level=low")),
    Step("Git-Hook aktiv", _hook_active),
)


HOOK_STEPS: Final = (Step("Arbeitsverzeichnis = Commit-Inhalt", _index_matches_worktree),)


def main(argv: list[str] | None = None) -> int:
    """Führt alle Schritte aus; Exit-Code 0 nur, wenn alle erfolgreich waren."""
    parser = argparse.ArgumentParser(description="Prüfbefehl des NeTEx CH Explorers.")
    parser.add_argument("--hook", action="store_true", help="Aufruf aus dem Git-Hook pre-commit")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    results: list[tuple[str, bool]] = []
    for step in (*HOOK_STEPS, *STEPS) if args.hook else STEPS:
        logger.info("==> %s", step.name)
        try:
            ok = step.run()
        except FileNotFoundError as error:
            logger.error("%s", error)
            ok = False
        results.append((step.name, ok))
    logger.info("Zusammenfassung:")
    for name, ok in results:
        logger.info("  %s  %s", "OK    " if ok else "FEHLER", name)
    failed = [name for name, ok in results if not ok]
    if failed:
        logger.error("Prüfbefehl nicht grün: %d Schritt(e) fehlgeschlagen.", len(failed))
        return 1
    logger.info("Prüfbefehl grün.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
