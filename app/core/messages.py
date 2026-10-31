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
    FILE_NAME_CHANGED = "file.name_changed"
    FILE_TYPE_UNSUPPORTED = "file.type_unsupported"
    FILE_EMPTY = "file.empty"
    FILE_TOO_LARGE = "file.too_large"
    FILE_TOTAL_TOO_LARGE = "file.total_too_large"
    FILE_WRITE_FAILED = "file.write_failed"
    ZIP_UNREADABLE = "zip.unreadable"
    ZIP_TOO_MANY_FILES = "zip.too_many_files"
    ZIP_TOTAL_TOO_LARGE = "zip.total_too_large"
    ZIP_ENTRY_TOO_LARGE = "zip.entry_too_large"
    ZIP_COMPRESSION_RATIO = "zip.compression_ratio"
    ZIP_UNSAFE_PATH = "zip.unsafe_path"
    ZIP_SYMLINK = "zip.symlink"
    ZIP_ENTRY_UNREADABLE = "zip.entry_unreadable"
    ZIP_ENTRIES_SKIPPED = "zip.entries_skipped"
    ZIP_NO_XML = "zip.no_xml"
    VERSION_NOT_NETEX = "version.not_netex"
    VERSION_NAMESPACE = "version.namespace"
    VERSION_ATTRIBUTE_110 = "version.attribute_110"
    VERSION_ATTRIBUTE_20 = "version.attribute_20"
    VERSION_ATTRIBUTE_OTHER = "version.attribute_other"
    VERSION_ATTRIBUTE_MISSING = "version.attribute_missing"
    VERSION_SCHEMA_LOCATION_110 = "version.schema_location_110"
    VERSION_SCHEMA_LOCATION_20 = "version.schema_location_20"
    VERSION_SCHEMA_LOCATION_GUIDE = "version.schema_location_guide"
    VERSION_SCHEMA_LOCATION_OTHER = "version.schema_location_other"
    VERSION_COMMENT_PROFILE = "version.comment_profile"
    VERSION_FILE_NAME_TYPE = "version.file_name_type"
    VERSION_STRUCTURE_CALLS = "version.structure_calls"
    VERSION_STRUCTURE_PATTERN = "version.structure_pattern"
    XSD_VIOLATION = "xsd.violation"
    XSD_UNCHECKABLE = "xsd.uncheckable"
    SCHEMATRON_NO_VERSION_ANY = "schematron.no_version_any"
    SCHEMATRON_NO_VERSIONREF_ANY = "schematron.no_versionref_any"
    SCHEMATRON_REF_REQUIRES_VERSION = "schematron.ref_elements_require_version"
    SCHEMATRON_NO_ORDER_ATTRIBUTE = "schematron.no_order_attribute"
    SCHEMATRON_VIOLATION = "schematron.violation"
    CORE_REQUIRED_MISSING = "core.required_missing"
    CORE_EXACTLY_ONE = "core.exactly_one"
    CORE_FORBIDDEN_PRESENT = "core.forbidden_present"
    CORE_VALUE_NOT_ALLOWED = "core.value_not_allowed"
    CORE_EXPECTED_MISSING = "core.expected_missing"
    CORE_STUB_JOURNEY = "core.stub_journey"
    VALIDATION_TRUNCATED = "validation.truncated"
    VALIDATION_FILE_SKIPPED_PROFILE = "validation.file_skipped_profile"
    VALIDATION_FILE_SKIPPED_UNREADABLE = "validation.file_skipped_unreadable"
    VALIDATION_STEP_UNAVAILABLE = "validation.step_unavailable"
    VALIDATION_STEP_NO_FILE = "validation.step_no_file"
    REFERENCE_UNRESOLVED = "reference.unresolved"
    REFERENCE_AMBIGUOUS = "reference.ambiguous"
    REFERENCE_EXTERNAL_OR_UNLOADED = "reference.external_or_unloaded"
    REFERENCE_VERSION_DIFFERS = "reference.version_differs"
    TIME_DEPARTURE_MISSING = "projection.time.departure_missing"
    TIME_DEPARTURE_INVALID = "projection.time.departure_invalid"
    TIME_DAY_OFFSET_INVALID = "projection.time.day_offset_invalid"
    TIME_DEMAND_MISSING = "projection.time.demand_missing"
    TIME_DEMAND_UNRESOLVED = "projection.time.demand_unresolved"
    TIME_TIMING_LINK_UNRESOLVED = "projection.time.timing_link_unresolved"
    TIME_TIMING_LINK_NOT_FOUND = "projection.time.timing_link_not_found"
    TIME_TIMING_LINK_AMBIGUOUS = "projection.time.timing_link_ambiguous"
    TIME_RUN_TIME_MISSING = "projection.time.run_time_missing"
    TIME_RUN_TIME_AMBIGUOUS = "projection.time.run_time_ambiguous"
    TIME_WAIT_TIME_MISSING = "projection.time.wait_time_missing"
    TIME_WAIT_TIME_AMBIGUOUS = "projection.time.wait_time_ambiguous"
    TIME_DURATION_INVALID = "projection.time.duration_invalid"
    TIME_STOP_UNAVAILABLE = "projection.time.stop_unavailable"
    TIMING_LINK_FROM_TO = "projection.timing_link_from_to"
    DAY_OFFSET_DEFAULT = "projection.day_offset_default"
    STOP_ORDER_DIFFERS = "projection.stop_order_differs"
    PART_TIME_DIFFERS = "projection.part_time_differs"
    DST_NIGHT_FORWARD = "projection.dst_night_forward"
    DST_NIGHT_BACK = "projection.dst_night_back"
    AVAILABILITY_ELEMENT_MISSING = "projection.availability_element_missing"
    AVAILABILITY_DATE_INVALID = "projection.availability_date_invalid"
    AVAILABILITY_RANGE_INVALID = "projection.availability_range_invalid"
    AVAILABILITY_BITS_INVALID = "projection.availability_bits_invalid"
    AVAILABILITY_BITS_LENGTH = "projection.availability_bits_length"
    NOTICE_UNASSIGNED = "projection.notice_unassigned"


@dataclass(frozen=True)
class Issue:
    """Eine Meldung mit Schweregrad, Schlüssel und Parametern für den Text."""

    severity: Severity
    key: MessageKey
    params: dict[str, ParamValue] = field(default_factory=dict)
