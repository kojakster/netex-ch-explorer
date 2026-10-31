"""XML einlesen mit pyexpat: jedes Element mit exakter Position.

Sicherheit (docs/engineering-guidelines.md): keine Parameter-Entitäten, keine externen Entitäten;
eine Datei mit `DOCTYPE` wird abgewiesen, bevor ihre Deklarationen gelesen werden.

Robustheit: Bei einem Syntaxfehler bleiben die bis dahin gelesenen Elemente erhalten; noch offene
Elemente haben kein Ende (`end` ist `None`). Fehler werden zu Diagnosen, nie zu Abstürzen.
"""

from __future__ import annotations

import hashlib
import re
from dataclasses import dataclass, field
from typing import Final
from xml.parsers import expat

from app.core.diagnostics import Diagnostic, DiagnosticCategory
from app.core.messages import MessageKey, Severity
from app.core.positions import Position, PositionTracker

UTF8_BOM: Final = b"\xef\xbb\xbf"
SUPPORTED_ENCODINGS: Final = frozenset({"utf-8", "utf8", "us-ascii", "ascii"})
_NAMESPACE_SEPARATOR: Final = " "
_XML_DECLARATION = re.compile(rb"^<\?xml[^>]*?encoding\s*=\s*[\"']([A-Za-z0-9._-]+)[\"']")


@dataclass(frozen=True)
class Comment:
    """Ein XML-Kommentar (für die Versionserkennung)."""

    text: str
    position: Position


@dataclass
class ElementRecord:
    """Ein Element mit Position.

    Attributes:
        index: Laufnummer in Dokumentreihenfolge (ab 0).
        parent: Index des Elternelements, `None` für das Wurzelelement.
        namespace: Namensraum-URI, `None` ohne Namensraum.
        name: Lokaler Name.
        attributes: Attribute; ohne Namensraum unter dem lokalen Namen, sonst `{uri}name`.
        text: Direkter Textinhalt (ohne Text der Kindelemente), unverändert.
        start: Position von `<`.
        end: Position direkt nach dem schliessenden `>`; `None`, wenn das Element nicht endet.
    """

    index: int
    parent: int | None
    depth: int
    namespace: str | None
    name: str
    attributes: dict[str, str]
    start: Position
    text: str = ""
    end: Position | None = None


@dataclass
class ParsedFile:
    """Ergebnis des Einlesens einer Datei."""

    name: str
    size: int
    sha256: str
    text: str
    elements: list[ElementRecord] = field(default_factory=list)
    comments: list[Comment] = field(default_factory=list)
    diagnostics: list[Diagnostic] = field(default_factory=list)

    @property
    def readable(self) -> bool:
        """Lesbar heisst: Die Datei hat mindestens ein Element und keinen Abbruch-Fehler."""
        return bool(self.elements) and not any(d.key in _FATAL_KEYS for d in self.diagnostics)


_FATAL_KEYS: Final = frozenset(
    {
        MessageKey.XML_SYNTAX_ERROR,
        MessageKey.XML_DOCTYPE_FORBIDDEN,
        MessageKey.XML_ENCODING_UNSUPPORTED,
    }
)


class _DoctypeError(Exception):
    """Interner Abbruch, sobald eine DOCTYPE-Deklaration beginnt."""


def _split_name(qualified: str) -> tuple[str | None, str]:
    namespace, separator, local = qualified.rpartition(_NAMESPACE_SEPARATOR)
    return (namespace, local) if separator else (None, qualified)


def _attribute_key(qualified: str) -> str:
    namespace, local = _split_name(qualified)
    return local if namespace is None else f"{{{namespace}}}{local}"


_WIDE_ENCODING_STARTS: Final = (
    (b"\x00\x00\xfe\xff", "utf-32"),
    (b"\xff\xfe\x00\x00", "utf-32"),
    (b"\xfe\xff", "utf-16"),
    (b"\xff\xfe", "utf-16"),
    (b"\x00<", "utf-16"),
    (b"<\x00", "utf-16"),
)


def _declared_encoding(data: bytes) -> str | None:
    """Kodierung aus BOM bzw. Byte-Muster (UTF-16/32) oder aus der XML-Deklaration."""
    for start, encoding in _WIDE_ENCODING_STARTS:
        if data.startswith(start):
            return encoding
    match = _XML_DECLARATION.match(data.removeprefix(UTF8_BOM)[:200])
    return match.group(1).decode("ascii").lower() if match else None


def _tag_end(data: bytes, start: int) -> int:
    """Byte direkt nach dem `>` eines Tags ab `start`; Anführungszeichen werden beachtet."""
    quote: int | None = None
    for offset in range(start, len(data)):
        byte = data[offset]
        if quote is not None:
            if byte == quote:
                quote = None
        elif byte in b"\"'":
            quote = byte
        elif byte == ord(">"):
            return offset + 1
    return len(data)


class _Reader:
    """Verarbeitet die Ereignisse von pyexpat für eine Datei."""

    def __init__(self, parsed: ParsedFile, data: bytes, text_start: int) -> None:
        self.parsed = parsed
        self.data = data
        self.tracker = PositionTracker(data, text_start)
        self.open: list[ElementRecord] = []
        # Gab es seit dem Start des innersten offenen Elements ein weiteres Ereignis?
        self.event_since_start = False
        self.text_parts: list[list[str]] = []
        self.parser = expat.ParserCreate(namespace_separator=_NAMESPACE_SEPARATOR)
        self.parser.SetParamEntityParsing(expat.XML_PARAM_ENTITY_PARSING_NEVER)
        self.parser.StartDoctypeDeclHandler = self._doctype
        self.parser.StartElementHandler = self._start
        self.parser.EndElementHandler = self._end
        self.parser.CharacterDataHandler = self._characters
        self.parser.CommentHandler = self._comment
        self.parser.ProcessingInstructionHandler = self._other_event

    def run(self) -> None:
        try:
            self.parser.Parse(self.data, True)
        except _DoctypeError:
            byte = self.parser.CurrentByteIndex
            declaration = self.data.rfind(b"<!DOCTYPE", 0, byte + 1)
            self._error(
                MessageKey.XML_DOCTYPE_FORBIDDEN, {}, declaration if declaration >= 0 else byte
            )
        except expat.ExpatError as error:
            detail = expat.ErrorString(error.code) or ""
            self._error(MessageKey.XML_SYNTAX_ERROR, {"detail": detail}, self.parser.ErrorByteIndex)

    def _error(self, key: MessageKey, params: dict[str, str | int], byte: int) -> None:
        position = self.tracker.position(byte) if byte >= 0 else None
        self.parsed.diagnostics.append(
            Diagnostic(DiagnosticCategory.XML_SYNTAX, Severity.ERROR, key, dict(params), position)
        )

    def _doctype(self, *_args: object) -> None:
        raise _DoctypeError

    def _start(self, qualified: str, attributes: dict[str, str]) -> None:
        self.event_since_start = True
        namespace, name = _split_name(qualified)
        parent = self.open[-1].index if self.open else None
        record = ElementRecord(
            index=len(self.parsed.elements),
            parent=parent,
            depth=len(self.open),
            namespace=namespace,
            name=name,
            attributes={_attribute_key(key): value for key, value in attributes.items()},
            start=self.tracker.position(self.parser.CurrentByteIndex),
        )
        self.parsed.elements.append(record)
        self.open.append(record)
        self.text_parts.append([])
        self.event_since_start = False

    def _end(self, _qualified: str) -> None:
        record = self.open.pop()
        record.text = "".join(self.text_parts.pop())
        byte = self.parser.CurrentByteIndex
        empty_tag = not self.event_since_start and self.data[byte - 2 : byte] == b"/>"
        end_byte = byte if empty_tag else _tag_end(self.data, byte)
        record.end = self.tracker.position(end_byte)
        self.event_since_start = True

    def _characters(self, text: str) -> None:
        self.event_since_start = True
        if self.text_parts:
            self.text_parts[-1].append(text)

    def _comment(self, text: str) -> None:
        self._other_event()
        position = self.tracker.position(self.parser.CurrentByteIndex)
        self.parsed.comments.append(Comment(text=text, position=position))

    def _other_event(self, *_args: object) -> None:
        self.event_since_start = True


def read_xml(name: str, data: bytes) -> ParsedFile:
    """Liest eine XML-Datei vollständig ein; Fehler werden zu Diagnosen."""
    text_start = len(UTF8_BOM) if data.startswith(UTF8_BOM) else 0
    parsed = ParsedFile(
        name=name,
        size=len(data),
        sha256=hashlib.sha256(data).hexdigest(),
        text=data[text_start:].decode("utf-8", errors="replace"),
    )
    encoding = _declared_encoding(data)
    if encoding is not None and encoding not in SUPPORTED_ENCODINGS:
        parsed.diagnostics.append(
            Diagnostic(
                DiagnosticCategory.FILE,
                Severity.ERROR,
                MessageKey.XML_ENCODING_UNSUPPORTED,
                {"encoding": encoding},
            )
        )
        return parsed
    _Reader(parsed, data, text_start).run()
    return parsed
