"""Schichtentest: `app/core` importiert weder die Server-Schicht noch Server-Bibliotheken."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from tests.support import PROJECT_ROOT

CORE_DIR = PROJECT_ROOT / "app" / "core"
FORBIDDEN = ("app.server", "app.frontend", "fastapi", "starlette", "uvicorn", "pydantic")


def imported_modules(path: Path) -> set[str]:
    tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.add(node.module)
    return modules


CORE_FILES = sorted(CORE_DIR.rglob("*.py"))


def test_core_files_found() -> None:
    assert CORE_FILES


@pytest.mark.parametrize("path", CORE_FILES, ids=lambda p: str(p.relative_to(PROJECT_ROOT)))
def test_core_does_not_import_server(path: Path) -> None:
    for module in imported_modules(path):
        assert not any(module == f or module.startswith(f"{f}.") for f in FORBIDDEN), module
