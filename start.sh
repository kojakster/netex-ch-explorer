#!/bin/sh
# Startet den NeTEx CH Explorer (macOS/Linux).
cd "$(dirname "$0")" && exec uv run python scripts/start.py "$@"
