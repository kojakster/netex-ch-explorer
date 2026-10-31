"""Ablage der benötigten Dateien im Guide-Klon `netexRealisationGuideSwitzerland`."""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Final

XSD_SUBMODULE_DIR: Final = PurePosixPath("xsd")
XSD_MAIN_FILE: Final = PurePosixPath("xsd/xsd/NeTEx_publication.xsd")
GENERAL_RULES_FILE: Final = PurePosixPath("src/schematron_rules/general_rules.sch")
TEMPLATES_DIR: Final = PurePosixPath("src/templates")
EXAMPLES_DIR: Final = PurePosixPath("src/examples")
MAPPING_TABLE_FILE: Final = PurePosixPath("src/media/Mappingtabellen_NeTEx_v2.0.xlsx")

XSD_FETCH_COMMAND: Final = "git submodule update --init --depth 1"

ANNEX_INDEX_FILE: Final = PurePosixPath("src/A5_annex_index.md")
GUIDE_REPOSITORY_URL: Final = "https://github.com/openTdataCH/netexRealisationGuideSwitzerland"

# Kapitel, auf die Regeln verweisen (Belege: docs/core-rules.md, docs/mapping.md D6).
CHAPTER_XML_MODELLING: Final = PurePosixPath("src/03_xml_modelling.md")
CHAPTER_TIMETABLE: Final = PurePosixPath("src/08_timetable.md")
CHAPTER_JOURNEY_PARTS: Final = PurePosixPath("src/uc05_journey_parts.md")
