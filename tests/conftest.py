"""Gemeinsame Fixtures: Projektpfade, Guide-Klon, synthetische Git-Ordner und Excel-Dateien."""

from __future__ import annotations

import os
import shutil
from collections.abc import Mapping, Sequence
from pathlib import Path

import pytest
from openpyxl import Workbook

from app.core.config import load_config
from app.core.guide.layout import EXAMPLES_DIR, MAPPING_TABLE_FILE, XSD_MAIN_FILE
from app.core.guide.mapping import SHEET_SPECS
from tests.support import (
    FIXTURES_DIR,
    PROJECT_ROOT,
    REQUIRE_GUIDE_ENV,
    SHA_A,
    SHA_B,
    GitRepoFactory,
    WorkbookFactory,
)


@pytest.fixture
def project_root() -> Path:
    return PROJECT_ROOT


@pytest.fixture
def guide_path() -> Path:
    """Pfad des echten Guide-Klons laut config/settings.json.

    Fehlt der Klon, wird der Test übersprungen; unter `scripts/test.py` schlägt er fehl.
    """
    path = load_config(PROJECT_ROOT).settings.guide_path
    if not (path / ".git").exists():
        message = f"Guide-Klon fehlt: {path}"
        if os.environ.get(REQUIRE_GUIDE_ENV) == "1":
            pytest.fail(message)
        pytest.skip(message)
    return path


def _write(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")


@pytest.fixture
def make_git_repo() -> GitRepoFactory:
    """Legt einen minimalen `.git`-Ordner an (ohne Git-Programm)."""

    def factory(
        work_tree: Path,
        *,
        branch: str | None = "next",
        commit: str | None = SHA_A,
        packed: bool = False,
    ) -> Path:
        git_dir = work_tree / ".git"
        git_dir.mkdir(parents=True)
        if branch is None:
            _write(git_dir / "HEAD", f"{commit}\n")
            return git_dir
        _write(git_dir / "HEAD", f"ref: refs/heads/{branch}\n")
        if commit is not None:
            if packed:
                _write(
                    git_dir / "packed-refs",
                    "# pack-refs with: peeled fully-peeled sorted\n"
                    f"{SHA_B} refs/remotes/origin/other\n"
                    f"{commit} refs/heads/{branch}\n"
                    f"^{SHA_B}\n",
                )
            else:
                _write(git_dir / "refs" / "heads" / branch, f"{commit}\n")
        return git_dir

    return factory


@pytest.fixture
def make_workbook() -> WorkbookFactory:
    """Schreibt eine synthetische Excel-Datei mit den angegebenen Blättern und Zeilen."""

    def factory(path: Path, sheets: Mapping[str, Sequence[Sequence[object]]]) -> Path:
        workbook = Workbook()
        default = workbook.active
        if default is not None:
            workbook.remove(default)
        for name, rows in sheets.items():
            sheet = workbook.create_sheet(name)
            for row in rows:
                sheet.append(list(row))
        path.parent.mkdir(parents=True, exist_ok=True)
        workbook.save(path)
        return path

    return factory


SYNTHETIC_EXAMPLES = ("ch20_three_stops.xml", "broken_xml.xml", "ch20_midnight.xml")


@pytest.fixture
def synthetic_guide(
    tmp_path: Path, make_git_repo: GitRepoFactory, make_workbook: WorkbookFactory
) -> Path:
    """Synthetischer Guide-Klon: Git, XSD-Submodul, Mappingtabelle, drei Beispiele mit README."""
    root = tmp_path / "guide"
    make_git_repo(root)
    make_git_repo(root / ".git" / "modules" / "xsd", branch=None, commit=SHA_B)
    xsd_work_tree = root / "xsd"
    xsd_work_tree.mkdir()
    (xsd_work_tree / ".git").write_text("gitdir: ../.git/modules/xsd/.git\n", encoding="utf-8")
    xsd_file = root.joinpath(*XSD_MAIN_FILE.parts)
    xsd_file.parent.mkdir(parents=True)
    xsd_file.write_text("<schema/>", encoding="utf-8")
    sheets = {spec.name: [list(spec.columns), ["x"] * len(spec.columns)] for spec in SHEET_SPECS}
    make_workbook(root.joinpath(*MAPPING_TABLE_FILE.parts), sheets)
    examples = root.joinpath(*EXAMPLES_DIR.parts)
    examples.mkdir(parents=True)
    for name in SYNTHETIC_EXAMPLES:
        shutil.copyfile(FIXTURES_DIR / name, examples / name)
    (examples / "README.md").write_text(
        "# Examples\n\n## Synthetische Fahrt\nText\n[Link](ch20_three_stops.xml)\n\n"
        "### Kaputt\n[Link](broken_xml.xml) und [nochmals](./ch20_three_stops.xml)\n",
        encoding="utf-8",
    )
    return root
