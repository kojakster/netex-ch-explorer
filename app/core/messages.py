"""Meldungen des Kerns: Schweregrad, Übersetzungsschlüssel und Parameter.

Der Kern erzeugt keine Texte. Jede Meldung besteht aus einem Schlüssel aus `MessageKey`
und Parametern; die Oberfläche setzt den Text aus der Sprachdatei ein.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum

type ParamValue = str | int


class Severity(StrEnum):
    """Schweregrad einer Meldung, vom schwersten zum leichtesten."""

    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class MessageKey(StrEnum):
    """Alle Übersetzungsschlüssel, die der Kern ausgibt.

    Ein Test stellt sicher, dass jeder Schlüssel in jeder Sprachdatei steht.
    """

    CONFIG_FILE_MISSING = "config.file_missing"
    CONFIG_FILE_INVALID = "config.file_invalid"
    CONFIG_VALUE_INVALID = "config.value_invalid"
    CONFIG_FIELD_UNKNOWN = "config.field_unknown"
    GUIDE_NOT_FOUND = "guide.not_found"
    GUIDE_NOT_GIT = "guide.not_git"
    GUIDE_GIT_UNREADABLE = "guide.git_unreadable"
    GUIDE_XSD_MISSING = "guide.xsd_missing"
    GUIDE_NEVER_TESTED = "guide.never_tested"
    GUIDE_TESTED_DIFFERS = "guide.tested_differs"
    GUIDE_TEST_RECORD_INVALID = "guide.test_record_invalid"
    MAPPING_FILE_MISSING = "mapping.file_missing"
    MAPPING_FILE_UNREADABLE = "mapping.file_unreadable"
    MAPPING_SHEET_MISSING = "mapping.sheet_missing"
    MAPPING_HEADER_NOT_FOUND = "mapping.header_not_found"
    MAPPING_COLUMN_MISSING = "mapping.column_missing"
    XML_SYNTAX_ERROR = "xml.syntax_error"
    XML_DOCTYPE_FORBIDDEN = "xml.doctype_forbidden"
    XML_ENCODING_UNSUPPORTED = "xml.encoding_unsupported"
    REFERENCE_UNRESOLVED = "reference.unresolved"
    REFERENCE_AMBIGUOUS = "reference.ambiguous"
    REFERENCE_EXTERNAL_OR_UNLOADED = "reference.external_or_unloaded"


@dataclass(frozen=True)
class Issue:
    """Eine Meldung mit Schweregrad, Schlüssel und Parametern für den Text."""

    severity: Severity
    key: MessageKey
    params: dict[str, ParamValue] = field(default_factory=dict)
