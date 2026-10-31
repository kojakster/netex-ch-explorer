"""Synthetische Testdateien: gekennzeichnet, im README beschrieben, wie beabsichtigt lesbar."""

from __future__ import annotations

from pathlib import Path
from xml.parsers import expat

import pytest

from tests.support import PROJECT_ROOT

FIXTURES = PROJECT_ROOT / "fixtures"
NOT_WELL_FORMED = {"broken_xml.xml"}
SECURITY = {"security_xxe.xml"}
XML_FILES = sorted(path for path in FIXTURES.glob("*.xml"))


def parse_without_dtd(path: Path) -> None:
    parser = expat.ParserCreate(namespace_separator=" ")
    parser.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_NEVER)
    parser.Parse(path.read_bytes(), True)


def test_fixtures_found() -> None:
    assert len(XML_FILES) >= 10


@pytest.mark.parametrize("path", XML_FILES, ids=lambda p: p.name)
def test_fixture_is_marked(path: Path) -> None:
    text = path.read_text(encoding="utf-8-sig")
    marker = "SICHERHEITSTEST" if path.name in SECURITY else "SYNTHETISCHE TESTDATEN"
    assert marker in text
    assert "<ParticipantRef>SYNTHETIC</ParticipantRef>" in text or path.name in SECURITY


@pytest.mark.parametrize("path", sorted(FIXTURES.iterdir()), ids=lambda p: p.name)
def test_fixture_is_documented(path: Path) -> None:
    if path.name == "README.md":
        return
    readme = (FIXTURES / "README.md").read_text(encoding="utf-8")
    assert f"`{path.name}`" in readme


@pytest.mark.parametrize(
    "path", [p for p in XML_FILES if p.name not in SECURITY], ids=lambda p: p.name
)
def test_fixture_well_formedness(path: Path) -> None:
    if path.name in NOT_WELL_FORMED:
        with pytest.raises(expat.ExpatError):
            parse_without_dtd(path)
    else:
        parse_without_dtd(path)
