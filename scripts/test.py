"""Führt alle Tests aus und schreibt bei vollem Erfolg `guide-tested.json`.

Die Tests mit dem Guide-Klon dürfen dabei nicht übersprungen werden (Umgebungsvariable
`NETEX_REQUIRE_GUIDE=1`); fehlt der Guide, schlägt der Lauf fehl. Zusätzliche Argumente gehen
an pytest; dann gilt der Lauf als Teillauf und der Nachweis wird nicht geschrieben.
Aufruf: `uv run python scripts/test.py`.
"""

from __future__ import annotations

import logging
import os
import subprocess
import sys
from pathlib import Path
from typing import Final

from app.core.config import load_config
from app.core.guide.guide_tested import (
    TEST_RECORD_FILE,
    ExampleRecord,
    GuideTestRecord,
    write_test_record,
)
from app.core.guide.status import analyze_examples, read_guide_revision

PROJECT_ROOT: Final = Path(__file__).resolve().parent.parent
REQUIRE_GUIDE_ENV: Final = "NETEX_REQUIRE_GUIDE"

logger = logging.getLogger("test")


def main(argv: list[str] | None = None) -> int:
    """Einstiegspunkt; gibt den Exit-Code zurück."""
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")
    pytest_args = sys.argv[1:] if argv is None else argv
    environment = {**os.environ, REQUIRE_GUIDE_ENV: "1"}
    result = subprocess.run(
        [sys.executable, "-m", "pytest", *pytest_args],
        cwd=PROJECT_ROOT,
        env=environment,
        check=False,
    )
    if result.returncode != 0:
        logger.error("Tests fehlgeschlagen; %s bleibt unverändert.", TEST_RECORD_FILE)
        return result.returncode
    if pytest_args:
        # Eigene pytest-Argumente können Tests abwählen (-k, -m, Pfade): kein vollständiger Lauf.
        logger.warning("Teillauf mit eigenen Argumenten; %s bleibt unverändert.", TEST_RECORD_FILE)
        return 0
    config = load_config(PROJECT_ROOT)
    revision = read_guide_revision(config.settings.guide_path)
    if revision.commit is None:
        logger.error("Guide-Commit nicht bestimmbar; %s bleibt unverändert.", TEST_RECORD_FILE)
        return 1
    examples = {
        status.name: ExampleRecord(status.sha256, status.result)
        for status in analyze_examples(config.settings.guide_path, None, config.ref_targets)
        if status.sha256 is not None
    }
    record = GuideTestRecord(revision.commit, revision.xsd_commit, examples)
    write_test_record(PROJECT_ROOT / TEST_RECORD_FILE, record)
    logger.info(
        "Alle Tests erfolgreich; %s geschrieben (Guide %s, XSD %s, %d Beispiele).",
        TEST_RECORD_FILE,
        revision.commit[:7],
        revision.xsd_commit[:7] if revision.xsd_commit else "-",
        len(examples),
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
