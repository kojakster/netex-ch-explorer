"""Diagnosen zu Dateien: Art, Schweregrad, Meldung und Stelle.

Die Arten werden nie vermischt (UMSETZUNGSPLAN Abschnitt 3, „Diagnosen getrennt“).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

from app.core.messages import MessageKey, ParamValue, Severity
from app.core.positions import Position


class DiagnosticCategory(StrEnum):
    """Art einer Diagnose."""

    FILE = "file"
    XML_SYNTAX = "xml_syntax"
    XSD = "xsd"
    PROFILE_RULE = "profile_rule"
    REFERENCE = "reference"
    PROJECTION = "projection"


@dataclass(frozen=True)
class Diagnostic:
    """Eine Diagnose zu einer Datei, optional mit Stelle."""

    category: DiagnosticCategory
    severity: Severity
    key: MessageKey
    params: dict[str, ParamValue] = field(default_factory=dict)
    position: Position | None = None
