"""Hilfeseite und Sprachdateien: nichts ohne Hilfetext, Sprachdateien vollständig.

Schlägt fehl, wenn eine Funktion, ein Prüfschritt, ein Schweregrad, eine Frame-Farbe oder ein
Meldungsschlüssel in einer Sprachdatei fehlt (Regel „Hilfeseite immer nachführen“).
"""

from __future__ import annotations

import json
from itertools import combinations
from pathlib import Path

import pytest

from app.core.config import DEFAULT_FRAME_COLORS, SUPPORTED_LANGUAGES
from app.core.diagnostics import DiagnosticCategory
from app.core.features import Feature
from app.core.guide.examples import ExampleResult
from app.core.guide.status import ExampleChange, GuideTestState
from app.core.index.references import ResolveStatus
from app.core.messages import MessageKey, Severity
from app.core.projection.common import LookupStatus
from app.core.validation.core_rules import RuleKind
from app.core.validation.detection import DetectionStatus, Evidence, ProfileVersion
from app.core.validation.steps import CHECK_STEPS, CheckStatus
from app.server.errors import ErrorKey
from tests.support import LOCALES_DIR


def load_messages(language: str) -> dict[str, str]:
    data = json.loads((LOCALES_DIR / f"{language}.json").read_text(encoding="utf-8"))
    assert isinstance(data, dict)
    return data


def required_keys() -> set[str]:
    keys = {str(key) for key in MessageKey} | {str(key) for key in ErrorKey}
    for feature in Feature:
        keys |= {f"feature.{feature}.title", f"feature.{feature}.description"}
    for step in CHECK_STEPS:
        keys |= {f"check.{step.id}.title", f"check.{step.id}.description"}
    keys |= {f"checkStatus.{status}" for status in CheckStatus}
    for severity in Severity:
        keys |= {f"severity.{severity}", f"severity.{severity}.description"}
    keys |= {f"guide.testState.{state}" for state in GuideTestState}
    keys |= {f"diagnostics.category.{category}" for category in DiagnosticCategory}
    keys |= {f"examples.result.{result}" for result in ExampleResult}
    keys |= {f"examples.change.{change}" for change in ExampleChange}
    keys |= {f"detection.status.{status}" for status in DetectionStatus}
    keys |= {f"detection.profile.{profile}" for profile in ProfileVersion}
    keys |= {f"detection.evidence.{evidence}" for evidence in Evidence}
    keys |= {f"coreRule.kind.{kind}" for kind in RuleKind}
    keys |= {f"lookup.{status}" for status in LookupStatus}
    keys |= {f"refs.status.{status}" for status in ResolveStatus}
    keys |= {f"language.{language}" for language in SUPPORTED_LANGUAGES}
    # NeTEx-Frame-Namen bleiben unübersetzt; nur die übrigen Farben brauchen einen Text.
    keys |= {f"frame.{key}" for key in DEFAULT_FRAME_COLORS if not key.endswith("Frame")}
    return keys


@pytest.mark.parametrize("language", SUPPORTED_LANGUAGES)
def test_every_help_and_message_key_is_translated(language: str) -> None:
    messages = load_messages(language)
    missing = sorted(required_keys() - messages.keys())
    assert missing == []


def test_language_files_have_identical_keys() -> None:
    reference = load_messages(SUPPORTED_LANGUAGES[0]).keys()
    for language in SUPPORTED_LANGUAGES[1:]:
        assert load_messages(language).keys() == reference


@pytest.mark.parametrize("language", SUPPORTED_LANGUAGES)
def test_no_empty_texts(language: str) -> None:
    assert all(text.strip() for text in load_messages(language).values())


def test_every_language_has_a_file() -> None:
    files = {path.stem for path in Path(LOCALES_DIR).glob("*.json")}
    assert files == set(SUPPORTED_LANGUAGES)


def test_check_step_ids_are_unique() -> None:
    ids = [step.id for step in CHECK_STEPS]
    assert len(ids) == len(set(ids))


def _linear(channel: int) -> float:
    value = channel / 255
    return value / 12.92 if value <= 0.04045 else ((value + 0.055) / 1.055) ** 2.4


def _rgb(color: str) -> tuple[float, float, float]:
    return (
        _linear(int(color[1:3], 16)),
        _linear(int(color[3:5], 16)),
        _linear(int(color[5:7], 16)),
    )


def _luminance(color: str) -> float:
    red, green, blue = _rgb(color)
    return 0.2126 * red + 0.7152 * green + 0.0722 * blue


def _lab(color: str) -> tuple[float, float, float]:
    red, green, blue = _rgb(color)
    x = (0.4124 * red + 0.3576 * green + 0.1805 * blue) / 0.95047
    y = 0.2126 * red + 0.7152 * green + 0.0722 * blue
    z = (0.0193 * red + 0.1192 * green + 0.9505 * blue) / 1.08883

    def f(t: float) -> float:
        return t ** (1 / 3) if t > 0.008856 else 7.787 * t + 16 / 116

    return 116 * f(y) - 16, 500 * (f(x) - f(y)), 200 * (f(y) - f(z))


def test_default_colors_have_readable_text() -> None:
    """Schriftkontrast ≥ 4,5:1 (WCAG AA) für jede Standardfarbe."""
    for color in DEFAULT_FRAME_COLORS.values():
        bright, dark = sorted((_luminance(color.background), _luminance(color.text)), reverse=True)
        assert (bright + 0.05) / (dark + 0.05) >= 4.5


def test_default_colors_are_distinct() -> None:
    """Kleinster Abstand ΔE76 zwischen zwei Standardfarben ≥ 33 (docs/decisions.md)."""
    for first, second in combinations(DEFAULT_FRAME_COLORS.values(), 2):
        lab_a, lab_b = _lab(first.background), _lab(second.background)
        distance = sum((a - b) ** 2 for a, b in zip(lab_a, lab_b, strict=True)) ** 0.5
        assert distance >= 33
