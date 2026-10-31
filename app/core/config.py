"""Einstellungen aus dem Ordner `config/` laden und prüfen.

Fehlt eine Datei oder ist ein Eintrag ungültig, gilt der Standardwert, und es entsteht
eine Meldung für die Oberfläche. Das Laden bricht nie ab.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Final

from app.core.messages import Issue, MessageKey, Severity

CONFIG_DIR_NAME: Final = "config"
SETTINGS_FILE: Final = "settings.json"
FRAME_COLORS_FILE: Final = "frame-colors.json"
NOT_RELEVANT_FILE: Final = "not-relevant-elements.json"
REF_TARGETS_FILE: Final = "ref-targets.json"

MAX_CONFIG_BYTES: Final = 1_000_000
SUPPORTED_LANGUAGES: Final = ("de-CH", "en")

_HEX_COLOR = re.compile(r"^#[0-9A-Fa-f]{6}$")
_XML_NAME = re.compile(r"[A-Za-z_][A-Za-z0-9_.-]*")
MIN_PORT: Final = 1024
MAX_PORT: Final = 65535


@dataclass(frozen=True)
class ZipLimits:
    """Grenzwerte für das Entpacken von ZIP-Dateien."""

    max_total_bytes: int = 200 * 1024 * 1024
    max_file_bytes: int = 50 * 1024 * 1024
    max_files: int = 500
    max_compression_ratio: int = 100


@dataclass(frozen=True)
class Settings:
    """Allgemeine Einstellungen; Pfade sind bereits absolut aufgelöst."""

    guide_path: Path
    netex_files_path: Path
    language: str
    port: int
    zip_limits: ZipLimits


@dataclass(frozen=True)
class FrameColor:
    """Hintergrund- und Schriftfarbe einer Frame-Markierung (`#RRGGBB`, Grossbuchstaben)."""

    background: str
    text: str


DEFAULT_GUIDE_PATH: Final = "../netexRealisationGuideSwitzerland"
DEFAULT_NETEX_FILES_PATH: Final = "../netex-files"
DEFAULT_LANGUAGE: Final = "de-CH"
DEFAULT_PORT: Final = 8765

DEFAULT_FRAME_COLORS: Final[dict[str, FrameColor]] = {
    "TimetableFrame": FrameColor("#0057B8", "#FFFFFF"),
    "ServiceFrame": FrameColor("#1B8A2F", "#000000"),
    "SiteFrame": FrameColor("#F57C00", "#000000"),
    "ServiceCalendarFrame": FrameColor("#FFD600", "#000000"),
    "ResourceFrame": FrameColor("#D32F2F", "#FFFFFF"),
    "CompositeFrame": FrameColor("#7B1FA2", "#FFFFFF"),
    "unknown": FrameColor("#6D4C2F", "#FFFFFF"),
    "notRelevant": FrameColor("#8A8A8A", "#000000"),
}

DEFAULT_NOT_RELEVANT_ELEMENTS: Final = (
    "SiteFacilitySet",
    "siteFacilitySets",
    "SiteFacilitySetRef",
    "PlaceEquipment",
    "placeEquipments",
    "EquipmentPlace",
    "equipmentPlaces",
    "LiftEquipmentRef",
    "SiteNavigationPath",
    "navigationPaths",
    "Access",
    "accesses",
    "AccessSpace",
    "accessSpaces",
    "entrances",
    "PointOfInterestClassification",
    "pointOfInterestClassifications",
    "PointOfInterestClassificationHierarchy",
    "pointOfInterestClassificationHierarchies",
    "PostalAddress",
    "addresses",
    "AssistanceServiceRef",
    "localServices",
    "TariffZone",
    "tariffZones",
)


@dataclass(frozen=True)
class AppConfig:
    """Alle geladenen Einstellungen und die Meldungen, die beim Laden entstanden."""

    settings: Settings
    frame_colors: dict[str, FrameColor]
    not_relevant_elements: tuple[str, ...]
    ref_targets: dict[str, tuple[str, ...]]
    issues: tuple[Issue, ...] = field(default=())


class _IssueCollector:
    """Sammelt Meldungen zu einer Einstellungsdatei."""

    def __init__(self, file_label: str) -> None:
        self.file_label = file_label
        self.issues: list[Issue] = []

    def add(self, key: MessageKey, field_name: str | None = None) -> None:
        params: dict[str, str | int] = {"file": self.file_label}
        if field_name is not None:
            params["field"] = field_name
        self.issues.append(Issue(Severity.WARNING, key, params))


def load_config(project_root: Path) -> AppConfig:
    """Lädt alle Einstellungsdateien aus `<project_root>/config/`.

    Relative Pfade in `settings.json` gelten relativ zu `project_root`.
    """
    config_dir = project_root / CONFIG_DIR_NAME
    settings, settings_issues = _load_settings(config_dir, project_root)
    frame_colors, color_issues = _load_frame_colors(config_dir)
    not_relevant, not_relevant_issues = _load_not_relevant(config_dir)
    ref_targets, ref_target_issues = _load_ref_targets(config_dir)
    return AppConfig(
        settings=settings,
        frame_colors=frame_colors,
        not_relevant_elements=not_relevant,
        ref_targets=ref_targets,
        issues=(*settings_issues, *color_issues, *not_relevant_issues, *ref_target_issues),
    )


def _read_json_object(path: Path, collector: _IssueCollector) -> dict[str, object] | None:
    """Liest eine JSON-Datei, deren oberste Ebene ein Objekt ist; sonst Meldung und `None`."""
    if not path.is_file():
        collector.add(MessageKey.CONFIG_FILE_MISSING)
        return None
    try:
        if path.stat().st_size > MAX_CONFIG_BYTES:
            collector.add(MessageKey.CONFIG_FILE_INVALID)
            return None
        data: object = json.loads(path.read_text(encoding="utf-8"))
    # RecursionError: sehr tief verschachteltes JSON.
    except (OSError, UnicodeDecodeError, json.JSONDecodeError, RecursionError):
        collector.add(MessageKey.CONFIG_FILE_INVALID)
        return None
    if not isinstance(data, dict):
        collector.add(MessageKey.CONFIG_FILE_INVALID)
        return None
    return data


def _report_unknown_fields(
    data: dict[str, object], known: tuple[str, ...], collector: _IssueCollector, prefix: str = ""
) -> None:
    for name in data:
        if name not in known:
            collector.add(MessageKey.CONFIG_FIELD_UNKNOWN, prefix + name)


def _text_value(
    data: dict[str, object], name: str, default: str, collector: _IssueCollector
) -> str:
    value = data.get(name, default)
    if isinstance(value, str) and value.strip():
        return value
    collector.add(MessageKey.CONFIG_VALUE_INVALID, name)
    return default


def _int_value(
    value: object,
    default: int,
    label: str,
    collector: _IssueCollector,
    bounds: tuple[int, int | None] = (1, None),
) -> int:
    """Gibt `value` zurück, wenn es eine ganze Zahl innerhalb `bounds` ist, sonst `default`."""
    minimum, maximum = bounds
    # bool ist in Python eine Unterklasse von int und wird ausdrücklich abgelehnt.
    if (
        isinstance(value, int)
        and not isinstance(value, bool)
        and value >= minimum
        and (maximum is None or value <= maximum)
    ):
        return value
    collector.add(MessageKey.CONFIG_VALUE_INVALID, label)
    return default


def _resolve_path(raw: str, project_root: Path) -> Path:
    path = Path(raw)
    return path if path.is_absolute() else (project_root / path).resolve()


def _load_settings(config_dir: Path, project_root: Path) -> tuple[Settings, list[Issue]]:
    collector = _IssueCollector(f"{CONFIG_DIR_NAME}/{SETTINGS_FILE}")
    data = _read_json_object(config_dir / SETTINGS_FILE, collector) or {}
    _report_unknown_fields(
        data, ("guidePath", "netexFilesPath", "language", "port", "zipLimits"), collector
    )
    guide_path = _text_value(data, "guidePath", DEFAULT_GUIDE_PATH, collector)
    netex_files_path = _text_value(data, "netexFilesPath", DEFAULT_NETEX_FILES_PATH, collector)
    language = _text_value(data, "language", DEFAULT_LANGUAGE, collector)
    if language not in SUPPORTED_LANGUAGES:
        collector.add(MessageKey.CONFIG_VALUE_INVALID, "language")
        language = DEFAULT_LANGUAGE
    port = _int_value(
        data.get("port", DEFAULT_PORT), DEFAULT_PORT, "port", collector, (MIN_PORT, MAX_PORT)
    )
    settings = Settings(
        guide_path=_resolve_path(guide_path, project_root),
        netex_files_path=_resolve_path(netex_files_path, project_root),
        language=language,
        port=port,
        zip_limits=_load_zip_limits(data.get("zipLimits"), "zipLimits" in data, collector),
    )
    return settings, collector.issues


def _load_zip_limits(raw: object, present: bool, collector: _IssueCollector) -> ZipLimits:
    defaults = ZipLimits()
    if not present:
        return defaults
    if not isinstance(raw, dict):
        collector.add(MessageKey.CONFIG_VALUE_INVALID, "zipLimits")
        return defaults
    fields = {
        "maxTotalBytes": defaults.max_total_bytes,
        "maxFileBytes": defaults.max_file_bytes,
        "maxFiles": defaults.max_files,
        "maxCompressionRatio": defaults.max_compression_ratio,
    }
    _report_unknown_fields(raw, tuple(fields), collector, prefix="zipLimits.")
    values = {
        name: _int_value(raw.get(name, default), default, f"zipLimits.{name}", collector)
        for name, default in fields.items()
    }
    return ZipLimits(
        max_total_bytes=values["maxTotalBytes"],
        max_file_bytes=values["maxFileBytes"],
        max_files=values["maxFiles"],
        max_compression_ratio=values["maxCompressionRatio"],
    )


def _load_frame_colors(config_dir: Path) -> tuple[dict[str, FrameColor], list[Issue]]:
    collector = _IssueCollector(f"{CONFIG_DIR_NAME}/{FRAME_COLORS_FILE}")
    data = _read_json_object(config_dir / FRAME_COLORS_FILE, collector)
    if data is None:
        return dict(DEFAULT_FRAME_COLORS), collector.issues
    _report_unknown_fields(data, tuple(DEFAULT_FRAME_COLORS), collector)
    colors: dict[str, FrameColor] = {}
    for key, default in DEFAULT_FRAME_COLORS.items():
        # Wie in settings.json: Ein fehlender Eintrag gilt still mit dem Standardwert.
        raw = data.get(key)
        colors[key] = default if raw is None else _frame_color(raw, key, default, collector)
    return colors, collector.issues


def _frame_color(
    raw: object, key: str, default: FrameColor, collector: _IssueCollector
) -> FrameColor:
    if not isinstance(raw, dict):
        collector.add(MessageKey.CONFIG_VALUE_INVALID, key)
        return default
    _report_unknown_fields(raw, ("background", "text"), collector, prefix=f"{key}.")
    background = _color_value(raw, "background", default.background, key, collector)
    text = _color_value(raw, "text", default.text, key, collector)
    return FrameColor(background=background, text=text)


def _color_value(
    raw: dict[str, object], name: str, default: str, key: str, collector: _IssueCollector
) -> str:
    value = raw.get(name)
    if isinstance(value, str) and _HEX_COLOR.match(value):
        return value.upper()
    collector.add(MessageKey.CONFIG_VALUE_INVALID, f"{key}.{name}")
    return default


def _load_not_relevant(config_dir: Path) -> tuple[tuple[str, ...], list[Issue]]:
    collector = _IssueCollector(f"{CONFIG_DIR_NAME}/{NOT_RELEVANT_FILE}")
    data = _read_json_object(config_dir / NOT_RELEVANT_FILE, collector)
    if data is None:
        return DEFAULT_NOT_RELEVANT_ELEMENTS, collector.issues
    _report_unknown_fields(data, ("elements",), collector)
    raw = data.get("elements")
    if not isinstance(raw, list):
        collector.add(MessageKey.CONFIG_VALUE_INVALID, "elements")
        return DEFAULT_NOT_RELEVANT_ELEMENTS, collector.issues
    elements: list[str] = []
    for index, value in enumerate(raw):
        if isinstance(value, str) and _XML_NAME.fullmatch(value):
            if value not in elements:
                elements.append(value)
        else:
            collector.add(MessageKey.CONFIG_VALUE_INVALID, f"elements[{index}]")
    return tuple(elements), collector.issues


def _load_ref_targets(config_dir: Path) -> tuple[dict[str, tuple[str, ...]], list[Issue]]:
    """Zieltypen von Referenzen, deren Name nicht dem Zieltyp entspricht (Entscheid „Zieltyp“)."""
    collector = _IssueCollector(f"{CONFIG_DIR_NAME}/{REF_TARGETS_FILE}")
    data = _read_json_object(config_dir / REF_TARGETS_FILE, collector)
    if data is None:
        return {}, collector.issues
    _report_unknown_fields(data, ("refs",), collector)
    raw = data.get("refs")
    if not isinstance(raw, dict):
        collector.add(MessageKey.CONFIG_VALUE_INVALID, "refs")
        return {}, collector.issues
    refs: dict[str, tuple[str, ...]] = {}
    for name, entry in raw.items():
        targets = _ref_entry_targets(name, entry, collector)
        if targets:
            refs[name] = targets
    return refs, collector.issues


def _ref_entry_targets(name: str, entry: object, collector: _IssueCollector) -> tuple[str, ...]:
    label = f"refs.{name}"
    if not _XML_NAME.fullmatch(name) or not isinstance(entry, dict):
        collector.add(MessageKey.CONFIG_VALUE_INVALID, label)
        return ()
    _report_unknown_fields(entry, ("targets", "xsdTypes"), collector, prefix=f"{label}.")
    targets = entry.get("targets")
    if (
        not isinstance(targets, list)
        or not targets
        or not all(isinstance(t, str) and _XML_NAME.fullmatch(t) for t in targets)
    ):
        collector.add(MessageKey.CONFIG_VALUE_INVALID, f"{label}.targets")
        return ()
    return tuple(dict.fromkeys(targets))
