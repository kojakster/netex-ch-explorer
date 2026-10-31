"""Funktionen der Anwendung. Aus dieser Liste entsteht der Abschnitt „Funktionen“ der Hilfeseite.

Jede Funktion braucht in jeder Sprachdatei `feature.<id>.title` und `feature.<id>.description`;
ein Test prüft das.
"""

from __future__ import annotations

from enum import StrEnum


class Feature(StrEnum):
    """Kennung einer Funktion der Oberfläche."""

    GUIDE_STATUS = "guide_status"
    FRAME_LEGEND = "frame_legend"
    LANGUAGE_SWITCH = "language_switch"
    HELP_PAGE = "help_page"
