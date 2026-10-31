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
    EXAMPLE_SELECTION = "example_selection"
    JOURNEY_LIST = "journey_list"
    OBJECT_SEARCH = "object_search"
    OBJECT_DETAIL = "object_detail"
    XML_VIEW = "xml_view"
    DIAGNOSTICS_LIST = "diagnostics_list"
    REFERENCES = "references"
    PROVENANCE_CHAIN = "provenance_chain"
    NAVIGATION_HISTORY = "navigation_history"
    JOURNEY_VIEW = "journey_view"
    CALCULATED_TIMES = "calculated_times"
    MIDNIGHT = "midnight"
    OPERATING_DAYS = "operating_days"
    OFFERS = "offers"
    NOTICES = "notices"
    MASTER_DATA = "master_data"
