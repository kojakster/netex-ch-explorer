"""Beim Start geladener Zustand des Servers."""

from __future__ import annotations

import logging
import threading
from pathlib import Path

from app.core.config import AppConfig, load_config
from app.core.guide.guide_tested import TEST_RECORD_FILE
from app.core.guide.links import GuideLinks, read_guide_links
from app.core.guide.status import GuideStatus, complete_examples, inspect_guide
from app.core.intake import WORK_DIR_NAME, Workspace
from app.core.validation.engine import ValidationEngine

logger = logging.getLogger(__name__)


class Runtime:
    """Einstellungen, Guide-Status, Prüfmaschine, Verweise und Arbeitsverzeichnis.

    Die XSD braucht rund 17 s zum Laden. `start_background` lädt sie und prüft die Beispiele in
    einem Hintergrundfaden; bis dahin zeigt `guide` die Beispiele ohne Ergebnis
    (`GuideStatus.examples_ready` ist `False`).
    """

    def __init__(
        self,
        config: AppConfig,
        guide: GuideStatus,
        work_dir: Path,
        test_record_path: Path | None = None,
        engine: ValidationEngine | None = None,
    ) -> None:
        self.config = config
        self.guide = guide
        self.workspace = Workspace(work_dir)
        self.engine = engine or ValidationEngine(guide.path, guide.revision.commit)
        self.links: GuideLinks = read_guide_links(guide.path)
        self._test_record_path = test_record_path

    def complete_examples(self) -> None:
        """Lädt die XSD und prüft die Beispiele (blockiert; für den Hintergrundfaden)."""
        self.engine.preload()
        if self._test_record_path is not None:
            self.guide = complete_examples(
                self.guide, self._test_record_path, self.config.ref_targets, self.engine
            )

    def start_background(self) -> threading.Thread:
        """Startet `complete_examples` in einem Hintergrundfaden."""
        thread = threading.Thread(target=self._run_background, name="guide-examples", daemon=True)
        thread.start()
        return thread

    def _run_background(self) -> None:
        try:
            self.complete_examples()
        except Exception:
            # Ein Fehler hier darf den Server nicht beenden; die Beispiele bleiben ohne Ergebnis.
            logger.exception("Prüfung der Beispiele fehlgeschlagen")


def load_runtime(project_root: Path, work_dir: Path | None = None) -> Runtime:
    """Lädt Einstellungen und untersucht den Guide-Klon (Beispiele erst im Hintergrund)."""
    config = load_config(project_root)
    record_path = project_root / TEST_RECORD_FILE
    guide = inspect_guide(
        config.settings.guide_path, record_path, config.ref_targets, defer_examples=True
    )
    return Runtime(config, guide, work_dir or project_root / WORK_DIR_NAME, record_path)
