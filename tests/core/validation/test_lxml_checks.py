"""XSD- und Schematron-Prüfung mit lxml: gehärteter Parser, einmaliges Laden, Befunde."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.core.validation.lxml_checks import (
    MAX_FINDINGS,
    NotCheckableError,
    RulesUnavailableError,
    SchematronChecker,
    XsdChecker,
    parse_safely,
)
from tests.support import FIXTURES_DIR

XSD = """<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" elementFormDefault="qualified">
  <xs:element name="a">
    <xs:complexType>
      <xs:sequence>
        <xs:element name="b" type="xs:int" maxOccurs="unbounded"/>
      </xs:sequence>
    </xs:complexType>
  </xs:element>
</xs:schema>"""

SCHEMATRON = """<schema xmlns="http://purl.oclc.org/dsdl/schematron">
  <pattern id="no_order_attribute">
    <rule context="*[@order]">
      <assert test="false()">
        The order attribute is not allowed (element: <value-of select="name()"/>)
      </assert>
    </rule>
  </pattern>
</schema>"""


def write(tmp_path: Path, name: str, text: str) -> Path:
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def test_parse_safely_reads_xml() -> None:
    assert parse_safely(b"<a><b>1</b></a>") is not None


@pytest.mark.parametrize("data", [b"<a>", b"", b"kein xml"])
def test_parse_safely_rejects_broken_xml(data: bytes) -> None:
    with pytest.raises(NotCheckableError):
        parse_safely(data)


def test_parse_safely_rejects_doctype_and_never_reads_entities() -> None:
    data = (FIXTURES_DIR / "security_xxe.xml").read_bytes()
    with pytest.raises(NotCheckableError) as error:
        parse_safely(data)
    assert "secret" not in str(error.value).lower() or "DOCTYPE" in str(error.value)
    internal = b'<!DOCTYPE a [<!ENTITY e "x">]><a>&e;</a>'
    with pytest.raises(NotCheckableError):
        parse_safely(internal)


class TestXsdChecker:
    def test_valid_and_invalid_documents(self, tmp_path: Path) -> None:
        checker = XsdChecker(write(tmp_path, "s.xsd", XSD))
        assert not checker.loaded
        assert checker.check(parse_safely(b"<a><b>1</b></a>")).findings == []
        assert checker.loaded
        outcome = checker.check(parse_safely(b"<a>\n<b>x</b>\n</a>"))
        [finding] = outcome.findings
        assert finding.line == 2
        assert finding.element == "b"
        assert "not a valid value" in finding.detail
        assert outcome.truncated == 0

    def test_loads_only_once(self, tmp_path: Path) -> None:
        checker = XsdChecker(write(tmp_path, "s.xsd", XSD))
        assert checker.load() is checker.load()

    def test_missing_file(self, tmp_path: Path) -> None:
        checker = XsdChecker(tmp_path / "fehlt.xsd")
        with pytest.raises(RulesUnavailableError):
            checker.check(parse_safely(b"<a/>"))
        assert not checker.loaded

    def test_broken_schema_is_remembered(self, tmp_path: Path) -> None:
        path = write(tmp_path, "s.xsd", "<xs:schema")
        checker = XsdChecker(path)
        with pytest.raises(RulesUnavailableError):
            checker.load()
        path.write_text(XSD, encoding="utf-8")
        with pytest.raises(RulesUnavailableError):
            checker.load()

    def test_invalid_schema_content(self, tmp_path: Path) -> None:
        checker = XsdChecker(write(tmp_path, "s.xsd", "<root/>"))
        with pytest.raises(RulesUnavailableError):
            checker.load()

    def test_findings_are_limited(self, tmp_path: Path) -> None:
        checker = XsdChecker(write(tmp_path, "s.xsd", XSD))
        body = "\n".join("<b>x</b>" for _ in range(MAX_FINDINGS + 25))
        outcome = checker.check(parse_safely(f"<a>\n{body}\n</a>".encode()))
        assert len(outcome.findings) == MAX_FINDINGS
        assert outcome.truncated == 25


class TestSchematronChecker:
    def test_reports_violations_with_line_and_element(self, tmp_path: Path) -> None:
        checker = SchematronChecker(write(tmp_path, "r.sch", SCHEMATRON))
        data = b'<a>\n  <b order="1"/>\n  <c/>\n  <d order="2"/>\n</a>'
        outcome = checker.check(parse_safely(data))
        assert [(f.line, f.element, f.rule) for f in outcome.findings] == [
            (2, "b", "no_order_attribute"),
            (4, "d", "no_order_attribute"),
        ]
        assert "order attribute is not allowed" in outcome.findings[0].detail

    def test_clean_document(self, tmp_path: Path) -> None:
        checker = SchematronChecker(write(tmp_path, "r.sch", SCHEMATRON))
        assert checker.check(parse_safely(b"<a><b/></a>")).findings == []

    def test_works_with_namespaces(self, tmp_path: Path) -> None:
        checker = SchematronChecker(write(tmp_path, "r.sch", SCHEMATRON))
        outcome = checker.check(parse_safely(b'<a xmlns="urn:x"><b order="1"/></a>'))
        assert [f.element for f in outcome.findings] == ["b"]

    def test_findings_are_limited(self, tmp_path: Path) -> None:
        checker = SchematronChecker(write(tmp_path, "r.sch", SCHEMATRON))
        body = "".join('<b order="1"/>' for _ in range(MAX_FINDINGS + 3))
        outcome = checker.check(parse_safely(f"<a>{body}</a>".encode()))
        assert len(outcome.findings) == MAX_FINDINGS
        assert outcome.truncated == 3

    def test_missing_file(self, tmp_path: Path) -> None:
        with pytest.raises(RulesUnavailableError):
            SchematronChecker(tmp_path / "fehlt.sch").check(parse_safely(b"<a/>"))

    def test_broken_rules_are_remembered(self, tmp_path: Path) -> None:
        path = write(tmp_path, "r.sch", "<schema")
        checker = SchematronChecker(path)
        for _ in range(2):
            with pytest.raises(RulesUnavailableError):
                checker.check(parse_safely(b"<a/>"))

    def test_invalid_rules(self, tmp_path: Path) -> None:
        checker = SchematronChecker(write(tmp_path, "r.sch", "<root/>"))
        with pytest.raises(RulesUnavailableError):
            checker.check(parse_safely(b"<a/>"))
