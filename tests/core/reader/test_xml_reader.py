from __future__ import annotations

import pytest

from app.core.diagnostics import DiagnosticCategory
from app.core.messages import MessageKey, Severity
from app.core.positions import PositionTracker
from app.core.reader.xml_reader import UTF8_BOM, ParsedFile, read_xml
from tests.support import FIXTURES_DIR

NS = "http://www.netex.org.uk/netex"


def slice_of(parsed: ParsedFile, name: str) -> str:
    element = next(e for e in parsed.elements if e.name == name)
    assert element.end is not None
    return parsed.text[element.start.char : element.end.char]


def test_positions_with_bom_and_multibyte_characters() -> None:
    data = (
        UTF8_BOM
        + (
            '<?xml version="1.0" encoding="UTF-8"?>\n'
            f'<a xmlns="{NS}">\n'
            '  <Name>Grüsse aus Zürich</Name><b x="1>2"/>\n'
            "  <ä/>\n"
            "</a>\n"
        ).encode()
    )
    parsed = read_xml("t.xml", data)
    assert parsed.readable
    assert parsed.text.startswith("<?xml")
    name = next(e for e in parsed.elements if e.name == "Name")
    assert (name.start.line, name.start.column) == (3, 3)
    assert name.start.byte == len(UTF8_BOM) + parsed.text.index("<Name>")
    assert slice_of(parsed, "Name") == "<Name>Grüsse aus Zürich</Name>"
    assert slice_of(parsed, "b") == '<b x="1>2"/>'
    b = next(e for e in parsed.elements if e.name == "b")
    assert b.start.column == len("  <Name>Grüsse aus Zürich</Name>") + 1
    assert slice_of(parsed, "ä") == "<ä/>"
    assert slice_of(parsed, "a").startswith("<a ") and slice_of(parsed, "a").endswith("</a>")


def test_empty_child_directly_before_end_tag() -> None:
    parsed = read_xml("t.xml", b"<a><b/></a>")
    assert slice_of(parsed, "b") == "<b/>"
    assert slice_of(parsed, "a") == "<a><b/></a>"


def test_explicit_empty_element() -> None:
    parsed = read_xml("t.xml", b'<a><b x="/"></b></a>')
    assert slice_of(parsed, "b") == '<b x="/"></b>'


def test_structure_namespaces_attributes_and_text() -> None:
    data = (
        f'<PublicationDelivery xmlns="{NS}" xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance"'
        ' version="2.1" xsi:schemaLocation="x y">'
        "<!-- Kommentar --><Name>  Bern <Text lang='fr'>Berne</Text></Name></PublicationDelivery>"
    ).encode()
    parsed = read_xml("t.xml", data)
    root, name, text = parsed.elements
    assert (root.parent, name.parent, text.parent) == (None, 0, 1)
    assert (root.depth, name.depth, text.depth) == (0, 1, 2)
    assert root.namespace == NS
    assert root.attributes == {
        "version": "2.1",
        "{http://www.w3.org/2001/XMLSchema-instance}schemaLocation": "x y",
    }
    assert name.text == "  Bern "
    assert text.text == "Berne"
    assert [comment.text for comment in parsed.comments] == [" Kommentar "]
    assert len(parsed.sha256) == 64
    assert parsed.size == len(data)


def test_syntax_error_keeps_elements_read_so_far() -> None:
    parsed = read_xml("broken_xml.xml", (FIXTURES_DIR / "broken_xml.xml").read_bytes())
    assert not parsed.readable
    assert parsed.elements
    [diagnostic] = parsed.diagnostics
    assert diagnostic.category is DiagnosticCategory.XML_SYNTAX
    assert diagnostic.severity is Severity.ERROR
    assert diagnostic.key is MessageKey.XML_SYNTAX_ERROR
    assert diagnostic.params == {"detail": "mismatched tag"}
    assert diagnostic.position is not None
    assert diagnostic.position.line == 48
    assert any(element.end is None for element in parsed.elements)


def test_doctype_is_rejected_without_reading_entities() -> None:
    parsed = read_xml("security_xxe.xml", (FIXTURES_DIR / "security_xxe.xml").read_bytes())
    assert not parsed.readable
    assert parsed.elements == []
    [diagnostic] = parsed.diagnostics
    assert diagnostic.key is MessageKey.XML_DOCTYPE_FORBIDDEN
    assert diagnostic.position is not None
    assert (diagnostic.position.line, diagnostic.position.column) == (5, 1)
    secret = (FIXTURES_DIR / "xxe_secret.txt").read_text(encoding="utf-8").strip()
    assert secret not in repr(parsed.elements)


def test_billion_laughs_is_rejected() -> None:
    data = (
        b'<?xml version="1.0"?><!DOCTYPE a [<!ENTITY a "x"><!ENTITY b "&a;&a;&a;&a;">]><a>&b;</a>'
    )
    parsed = read_xml("t.xml", data)
    assert [d.key for d in parsed.diagnostics] == [MessageKey.XML_DOCTYPE_FORBIDDEN]


@pytest.mark.parametrize("encoding", ["ISO-8859-1", "windows-1252", "UTF-16"])
def test_unsupported_encoding(encoding: str) -> None:
    parsed = read_xml("t.xml", f'<?xml version="1.0" encoding="{encoding}"?><a/>'.encode())
    assert not parsed.readable
    [diagnostic] = parsed.diagnostics
    assert diagnostic.category is DiagnosticCategory.FILE
    assert diagnostic.params == {"encoding": encoding.lower()}


@pytest.mark.parametrize(
    ("data", "encoding"),
    [
        ("<r><a/></r>".encode("utf-16"), "utf-16"),
        ("<r/>".encode("utf-16-le"), "utf-16"),
        ("<r/>".encode("utf-16-be"), "utf-16"),
        ("<r/>".encode("utf-32"), "utf-32"),
    ],
)
def test_wide_encodings_are_rejected(data: bytes, encoding: str) -> None:
    parsed = read_xml("t.xml", data)
    assert not parsed.readable
    assert [(d.key, d.params) for d in parsed.diagnostics] == [
        (MessageKey.XML_ENCODING_UNSUPPORTED, {"encoding": encoding})
    ]


def test_empty_file_is_unreadable() -> None:
    parsed = read_xml("leer.xml", b"")
    assert not parsed.readable
    assert [d.key for d in parsed.diagnostics] == [MessageKey.XML_SYNTAX_ERROR]


def test_processing_instruction_counts_as_content() -> None:
    parsed = read_xml("t.xml", b"<a><?pi daten?></a>")
    assert slice_of(parsed, "a") == "<a><?pi daten?></a>"


def test_tracker_handles_backward_offsets() -> None:
    data = "äb\ncd".encode()
    tracker = PositionTracker(data, 0)
    late = tracker.position(len(data))
    early = tracker.position(2)
    assert (late.line, late.column, late.char) == (2, 3, 5)
    assert (early.line, early.column, early.char) == (1, 2, 1)
