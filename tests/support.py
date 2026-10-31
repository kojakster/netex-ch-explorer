"""Konstanten für die Tests."""

from __future__ import annotations

from collections.abc import Callable, Mapping, Sequence
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
FIXTURES_DIR = PROJECT_ROOT / "fixtures"
LOCALES_DIR = PROJECT_ROOT / "app" / "frontend" / "src" / "locales"
REQUIRE_GUIDE_ENV = "NETEX_REQUIRE_GUIDE"

SHA_A = "a" * 40
SHA_B = "b" * 40

type GitRepoFactory = Callable[..., Path]
type WorkbookFactory = Callable[[Path, Mapping[str, Sequence[Sequence[object]]]], Path]
