"""Hilfeseite und Sprachdateien: nichts ohne Hilfetext, Sprachdateien vollständig.

Schlägt fehl, wenn eine Funktion, ein Prüfschritt, ein Schweregrad, eine Frame-Farbe oder ein
Meldungsschlüssel in einer Sprachdatei fehlt (Regel „Hilfeseite immer nachführen“).
"""

from __future__ import annotations

import ast
import json
import re
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
from tests.support import LOCALES_DIR, PROJECT_ROOT


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


# Quelltext, in dem Übersetzungsschlüssel vorkommen können: Kern, Server und Oberfläche ohne Tests.
_FRONTEND_SOURCE = PROJECT_ROOT / "app" / "frontend" / "src"
_TEMPLATE_KEY = re.compile(r"`([a-z][A-Za-z]*\.[^`]*\$\{[^`]*)`")
_PLACEHOLDER = re.compile(r"\$\{[^}]*\}")


_BLOCK_COMMENT = re.compile(r"/\*.*?\*/", re.DOTALL)
_LINE_COMMENT = re.compile(r"(?m)^\s*//.*$")


def _python_strings(path: Path) -> list[str]:
    """Zeichenketten des Python-Codes ohne Docstrings (Kommentare kennt `ast` nicht)."""
    tree = ast.parse(path.read_text(encoding="utf-8"))
    docstrings = {
        id(node.body[0].value)
        for node in ast.walk(tree)
        if isinstance(node, ast.Module | ast.ClassDef | ast.FunctionDef | ast.AsyncFunctionDef)
        and node.body
        and isinstance(node.body[0], ast.Expr)
        and isinstance(node.body[0].value, ast.Constant)
    }
    return [
        node.value
        for node in ast.walk(tree)
        if isinstance(node, ast.Constant)
        and isinstance(node.value, str)
        and id(node) not in docstrings
    ]


def _typescript_code(path: Path) -> str:
    """TypeScript-Quelltext ohne Block- und Zeilenkommentare (ganze Kommentarzeilen)."""
    text = _BLOCK_COMMENT.sub("", path.read_text(encoding="utf-8"))
    return _LINE_COMMENT.sub("", text)


def _source_texts() -> list[str]:
    """Zeichenketten des Anwendungscodes: ohne Kommentare, Docstrings und Testdateien."""
    texts = [
        text for path in (PROJECT_ROOT / "app").rglob("*.py") for text in _python_strings(path)
    ]
    texts += [
        _typescript_code(path)
        for pattern in ("*.ts", "*.tsx")
        for path in _FRONTEND_SOURCE.rglob(pattern)
        if ".test." not in path.name
    ]
    return texts


def _key_patterns(texts: list[str]) -> list[re.Pattern[str]]:
    """Zusammengesetzte Schlüssel der Oberfläche (`feature.${id}.title`) als Muster."""
    templates = {match for text in texts for match in _TEMPLATE_KEY.findall(text)}
    return [
        re.compile(
            "".join(
                r"[\w-]+" if part is None else re.escape(part)
                for part in _split_placeholders(template)
            )
            + "$"
        )
        for template in templates
    ]


def _split_placeholders(template: str) -> list[str | None]:
    parts: list[str | None] = []
    position = 0
    for match in _PLACEHOLDER.finditer(template):
        parts.append(template[position : match.start()])
        parts.append(None)
        position = match.end()
    parts.append(template[position:])
    return parts


def _mentions(text: str, key: str) -> bool:
    """Python-Zeichenkette ist der Schlüssel selbst; im TypeScript steht er in Anführungszeichen."""
    return text == key or f'"{key}"' in text


def test_no_unused_texts() -> None:
    """Jeder Schlüssel der Sprachdateien wird gebraucht: im Code als Text, als Schlüssel einer
    Aufzählung bzw. Liste (Hilfeseiten-Test) oder über einen zusammengesetzten Schlüssel."""
    texts = _source_texts()
    patterns = _key_patterns(texts)
    required = required_keys()
    unused = sorted(
        key
        for key in load_messages(SUPPORTED_LANGUAGES[0])
        if key not in required
        and not any(_mentions(text, key) for text in texts)
        and not any(pattern.match(key) for pattern in patterns)
    )
    assert unused == []


def test_unused_texts_are_detected() -> None:
    """Der Test darf nicht leer laufen: ein erfundener Schlüssel wird nicht als benutzt erkannt."""
    texts = _source_texts()
    patterns = _key_patterns(texts)
    assert patterns
    assert not any(pattern.match("nirgends.verwendet") for pattern in patterns)
    assert not any(_mentions(text, "nirgends.verwendet") for text in texts)


def test_every_composed_key_pattern_matches_a_text() -> None:
    """Auch zusammengesetzte Schlüssel (`feature.${id}.title`) müssen Texte finden."""
    keys = load_messages(SUPPORTED_LANGUAGES[0]).keys()
    patterns = _key_patterns(_source_texts())
    assert [pattern.pattern for pattern in patterns if not any(map(pattern.match, keys))] == []


def test_comments_and_docstrings_do_not_count_as_use(tmp_path: Path) -> None:
    """Ein Schlüssel nur in Kommentar oder Docstring gilt nicht als benutzt."""
    python = tmp_path / "modul.py"
    python.write_text('"""Doc mit a.b."""\n# a.c\nWERT = "a.d"\n', encoding="utf-8")
    assert _python_strings(python) == ["a.d"]
    typescript = tmp_path / "datei.ts"
    typescript.write_text('// "a.b"\n/* "a.c" */\nconst x = "a.d";\n', encoding="utf-8")
    assert _mentions(_typescript_code(typescript), "a.d")
    assert not _mentions(_typescript_code(typescript), "a.b")
    assert not _mentions(_typescript_code(typescript), "a.c")
