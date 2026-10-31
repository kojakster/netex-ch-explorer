"""Startet den NeTEx CH Explorer lokal.

Baut die Oberfläche, wenn sie fehlt oder älter als ihre Quellen ist, und startet den Server
auf 127.0.0.1. Aufruf: `uv run python scripts/start.py` (oder `start.sh` / `start.ps1`).
"""

from __future__ import annotations

import argparse
import logging
import shutil
import subprocess
import sys
import threading
import webbrowser
from pathlib import Path
from typing import Final

import uvicorn
from frontend import FRONTEND_DIR, PROJECT_ROOT, dependencies_need_install, frontend_needs_build

from app.core.config import MAX_PORT, MIN_PORT
from app.server.app import FRONTEND_DIST, create_app
from app.server.runtime import load_runtime
from app.server.security import LOCAL_HOST

BROWSER_DELAY_SECONDS: Final = 1.5

logger = logging.getLogger("start")


def build_frontend(frontend_dir: Path) -> bool:
    """Installiert bei Bedarf die Pakete und baut die Oberfläche; `False` bei Fehler."""
    npm = shutil.which("npm")
    if npm is None:
        logger.error("npm wurde nicht gefunden. Bitte Node.js 22 installieren (siehe README).")
        return False
    if dependencies_need_install(frontend_dir):
        logger.info("Installiere Pakete der Oberfläche (npm ci) …")
        if subprocess.run([npm, "ci"], cwd=frontend_dir, check=False).returncode != 0:
            logger.error("npm ci ist fehlgeschlagen.")
            return False
    logger.info("Baue die Oberfläche (npm run build) …")
    if subprocess.run([npm, "run", "build"], cwd=frontend_dir, check=False).returncode != 0:
        logger.error("Der Build der Oberfläche ist fehlgeschlagen.")
        return False
    return True


def _port(value: str) -> int:
    port = int(value)
    if not MIN_PORT <= port <= MAX_PORT:
        message = f"Port muss zwischen {MIN_PORT} und {MAX_PORT} liegen"
        raise argparse.ArgumentTypeError(message)
    return port


def main(argv: list[str] | None = None) -> int:
    """Einstiegspunkt; gibt den Exit-Code zurück."""
    parser = argparse.ArgumentParser(description="Startet den NeTEx CH Explorer lokal.")
    parser.add_argument("--port", type=_port, help="Port (Standard aus config/settings.json)")
    parser.add_argument("--no-browser", action="store_true", help="Browser nicht öffnen")
    args = parser.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(levelname)s %(name)s: %(message)s")

    if frontend_needs_build(FRONTEND_DIR) and not build_frontend(FRONTEND_DIR):
        return 1
    runtime = load_runtime(PROJECT_ROOT)
    port: int = args.port or runtime.config.settings.port
    app = create_app(runtime, PROJECT_ROOT / FRONTEND_DIST, port)
    # XSD laden und Beispiele prüfen (rund 20 Sekunden); die Oberfläche zeigt den Stand an.
    runtime.start_background()
    url = f"http://{LOCAL_HOST}:{port}/"
    logger.info("NeTEx CH Explorer läuft unter %s (beenden mit Ctrl+C)", url)
    if not args.no_browser:
        timer = threading.Timer(BROWSER_DELAY_SECONDS, webbrowser.open, args=(url,))
        timer.daemon = True
        timer.start()
    uvicorn.run(app, host=LOCAL_HOST, port=port, log_level="info")
    return 0


if __name__ == "__main__":
    sys.exit(main())
