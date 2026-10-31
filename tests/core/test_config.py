from __future__ import annotations

import json
from pathlib import Path

import pytest

from app.core.config import (
    DEFAULT_FRAME_COLORS,
    DEFAULT_NOT_RELEVANT_ELEMENTS,
    MAX_CONFIG_BYTES,
    ZipLimits,
    load_config,
)
from app.core.messages import MessageKey, Severity


def write_config(root: Path, name: str, content: object) -> None:
    config_dir = root / "config"
    config_dir.mkdir(exist_ok=True)
    text = content if isinstance(content, str) else json.dumps(content)
    (config_dir / name).write_text(text, encoding="utf-8")


def issue_fields(root: Path) -> list[tuple[MessageKey, str | int | None]]:
    return [(issue.key, issue.params.get("field")) for issue in load_config(root).issues]


def test_project_config_matches_defaults(project_root: Path) -> None:
    config = load_config(project_root)
    assert config.issues == ()
    assert config.frame_colors == DEFAULT_FRAME_COLORS
    assert config.not_relevant_elements == DEFAULT_NOT_RELEVANT_ELEMENTS
    assert config.settings.zip_limits == ZipLimits()
    assert (
        config.settings.guide_path
        == (project_root / "../netexRealisationGuideSwitzerland").resolve()
    )


def test_missing_files_give_defaults_and_warnings(tmp_path: Path) -> None:
    config = load_config(tmp_path)
    assert config.frame_colors == DEFAULT_FRAME_COLORS
    assert config.not_relevant_elements == DEFAULT_NOT_RELEVANT_ELEMENTS
    assert config.settings.language == "de-CH"
    assert config.settings.port == 8765
    assert [issue.key for issue in config.issues] == [MessageKey.CONFIG_FILE_MISSING] * 4
    assert all(issue.severity is Severity.WARNING for issue in config.issues)
    assert config.issues[0].params == {"file": "config/settings.json"}


@pytest.mark.parametrize("content", ["{kaputt", "[]", '"text"'])
def test_invalid_json_is_reported(tmp_path: Path, content: str) -> None:
    write_config(tmp_path, "settings.json", content)
    assert (MessageKey.CONFIG_FILE_INVALID, None) in issue_fields(tmp_path)


def test_too_large_file_is_rejected(tmp_path: Path) -> None:
    write_config(tmp_path, "settings.json", " " * (MAX_CONFIG_BYTES + 1))
    assert (MessageKey.CONFIG_FILE_INVALID, None) in issue_fields(tmp_path)


def test_non_utf8_file_is_rejected(tmp_path: Path) -> None:
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "settings.json").write_bytes(b"\xff\xfe{")
    assert (MessageKey.CONFIG_FILE_INVALID, None) in issue_fields(tmp_path)


def test_settings_values_are_validated(tmp_path: Path) -> None:
    write_config(
        tmp_path,
        "settings.json",
        {
            "guidePath": "",
            "netexFilesPath": 3,
            "language": "fr-CH",
            "port": 80,
            "zipLimits": {"maxFiles": True, "maxFileBytes": -1, "extra": 1},
            "typo": 1,
        },
    )
    config = load_config(tmp_path)
    fields = issue_fields(tmp_path)
    for field in ("guidePath", "netexFilesPath", "language", "port"):
        assert (MessageKey.CONFIG_VALUE_INVALID, field) in fields
    assert (MessageKey.CONFIG_VALUE_INVALID, "zipLimits.maxFiles") in fields
    assert (MessageKey.CONFIG_VALUE_INVALID, "zipLimits.maxFileBytes") in fields
    assert (MessageKey.CONFIG_FIELD_UNKNOWN, "zipLimits.extra") in fields
    assert (MessageKey.CONFIG_FIELD_UNKNOWN, "typo") in fields
    assert config.settings.language == "de-CH"
    assert config.settings.port == 8765
    assert config.settings.zip_limits == ZipLimits()


def test_valid_settings_are_used(tmp_path: Path) -> None:
    absolute = tmp_path / "guide"
    write_config(
        tmp_path,
        "settings.json",
        {
            "guidePath": str(absolute),
            "netexFilesPath": "daten",
            "language": "en",
            "port": 9000,
            "zipLimits": {"maxFiles": 7},
        },
    )
    settings = load_config(tmp_path).settings
    assert settings.guide_path == absolute
    assert settings.netex_files_path == (tmp_path / "daten").resolve()
    assert settings.language == "en"
    assert settings.port == 9000
    assert settings.zip_limits.max_files == 7
    assert settings.zip_limits.max_total_bytes == ZipLimits().max_total_bytes


def test_zip_limits_must_be_object(tmp_path: Path) -> None:
    write_config(tmp_path, "settings.json", {"zipLimits": 5})
    assert (MessageKey.CONFIG_VALUE_INVALID, "zipLimits") in issue_fields(tmp_path)


def test_frame_colors_fall_back_per_entry(tmp_path: Path) -> None:
    colors: dict[str, object] = {
        key: {"background": c.background, "text": c.text} for key, c in DEFAULT_FRAME_COLORS.items()
    }
    colors["SiteFrame"] = {"background": "#abcdef", "text": "#000000"}
    colors["ServiceFrame"] = {"background": "grün", "text": "#000000", "x": 1}
    colors["ResourceFrame"] = "rot"
    del colors["CompositeFrame"]
    colors["FooFrame"] = {"background": "#000000", "text": "#FFFFFF"}
    write_config(tmp_path, "frame-colors.json", colors)
    config = load_config(tmp_path)
    fields = issue_fields(tmp_path)
    assert config.frame_colors["SiteFrame"].background == "#ABCDEF"
    assert config.frame_colors["ServiceFrame"] == DEFAULT_FRAME_COLORS["ServiceFrame"]
    assert config.frame_colors["ResourceFrame"] == DEFAULT_FRAME_COLORS["ResourceFrame"]
    assert config.frame_colors["CompositeFrame"] == DEFAULT_FRAME_COLORS["CompositeFrame"]
    assert list(config.frame_colors) == list(DEFAULT_FRAME_COLORS)
    assert (MessageKey.CONFIG_VALUE_INVALID, "ServiceFrame.background") in fields
    assert (MessageKey.CONFIG_FIELD_UNKNOWN, "ServiceFrame.x") in fields
    assert (MessageKey.CONFIG_VALUE_INVALID, "ResourceFrame") in fields
    # Fehlender Eintrag: Standardwert ohne Meldung (wie in settings.json).
    assert not any(field == "CompositeFrame" for _, field in fields)
    assert (MessageKey.CONFIG_FIELD_UNKNOWN, "FooFrame") in fields


def test_not_relevant_elements_are_validated(tmp_path: Path) -> None:
    write_config(
        tmp_path,
        "not-relevant-elements.json",
        {"elements": ["TariffZone", "TariffZone", "<script>", 5, "ok.name"], "x": 1},
    )
    config = load_config(tmp_path)
    fields = issue_fields(tmp_path)
    assert config.not_relevant_elements == ("TariffZone", "ok.name")
    assert (MessageKey.CONFIG_VALUE_INVALID, "elements[2]") in fields
    assert (MessageKey.CONFIG_VALUE_INVALID, "elements[3]") in fields
    assert (MessageKey.CONFIG_FIELD_UNKNOWN, "x") in fields


def test_not_relevant_elements_must_be_list(tmp_path: Path) -> None:
    write_config(tmp_path, "not-relevant-elements.json", {"elements": "TariffZone"})
    config = load_config(tmp_path)
    assert config.not_relevant_elements == DEFAULT_NOT_RELEVANT_ELEMENTS
    assert (MessageKey.CONFIG_VALUE_INVALID, "elements") in issue_fields(tmp_path)


def test_deeply_nested_json_is_rejected(tmp_path: Path) -> None:
    write_config(tmp_path, "settings.json", "[" * 200_000)
    assert (MessageKey.CONFIG_FILE_INVALID, None) in issue_fields(tmp_path)
