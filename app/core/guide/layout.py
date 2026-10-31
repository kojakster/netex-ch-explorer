"""Ablage der benötigten Dateien im Guide-Klon `netexRealisationGuideSwitzerland`."""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import Final

XSD_SUBMODULE_DIR: Final = PurePosixPath("xsd")
XSD_MAIN_FILE: Final = PurePosixPath("xsd/xsd/NeTEx_publication.xsd")
GENERAL_RULES_FILE: Final = PurePosixPath("src/schematron_rules/general_rules.sch")
TEMPLATES_DIR: Final = PurePosixPath("src/templates")
MAPPING_TABLE_FILE: Final = PurePosixPath("src/media/Mappingtabellen_NeTEx_v2.0.xlsx")

XSD_FETCH_COMMAND: Final = "git submodule update --init --depth 1"
