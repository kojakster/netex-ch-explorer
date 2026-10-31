"""Beim Start geladener Zustand des Servers."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path

from app.core.config import AppConfig, load_config
from app.core.guide.guide_tested import TEST_RECORD_FILE
from app.core.guide.status import GuideStatus, inspect_guide


@dataclass(frozen=True)
class Runtime:
    """Einstellungen und Guide-Status (inklusive Beispiele), einmal beim Start ermittelt."""

    config: AppConfig
    guide: GuideStatus


def load_runtime(project_root: Path) -> Runtime:
    """Lädt Einstellungen und untersucht den Guide-Klon."""
    config = load_config(project_root)
    guide = inspect_guide(
        config.settings.guide_path, project_root / TEST_RECORD_FILE, config.ref_targets
    )
    return Runtime(config=config, guide=guide)
