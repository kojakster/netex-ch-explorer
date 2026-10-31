"""XSD- und Schematron-Prüfung mit lxml.

Sicherheit (docs/engineering-guidelines.md): lxml liest Dateien nur mit `resolve_entities=False`,
`no_network=True`, `load_dtd=False` und ohne `huge_tree`; Dateien mit `DOCTYPE` weist der Einleser
(`app/core/reader/xml_reader.py`) vorher ab, und `parse_safely` weist sie ein zweites Mal ab.

Die XSD (ca. 17 s Ladezeit) und die Schematron-Regeln werden einmal geladen und wiederverwendet.
lxml-Prüfer sind nicht threadsicher (Fehlerprotokoll am Objekt); ein Sperre serialisiert Prüfungen.
"""

from __future__ import annotations

import io
import logging
import re
import threading
from dataclasses import dataclass
from pathlib import Path
from typing import Final, NewType, cast

from lxml import etree, isoschematron

logger = logging.getLogger(__name__)

NETEX_NAMESPACE_PREFIX: Final = "{http://www.netex.org.uk/netex}"
MAX_FINDINGS: Final = 500
_MAX_DETAIL: Final = 500
_ELEMENT_IN_MESSAGE = re.compile(r"Element '(?:\{[^}]*\})?([^'{}]+)'")
_SVRL: Final = "{http://purl.oclc.org/dsdl/svrl}"


# Ein eingelesenes Dokument; lxml hat keine Typangaben, der Name hält die Aufrufer typsicher.
ParsedDocument = NewType("ParsedDocument", object)


class RulesUnavailableError(Exception):
    """XSD oder Schematron-Regeln lassen sich nicht laden (fehlen oder sind fehlerhaft)."""


class NotCheckableError(Exception):
    """lxml kann die Datei nicht lesen oder weist sie ab (z. B. DOCTYPE)."""


@dataclass(frozen=True)
class RawFinding:
    """Ein Befund einer lxml-Prüfung: Zeile, Elementname und Text (Originalwortlaut)."""

    line: int
    element: str | None
    detail: str
    rule: str | None = None


@dataclass(frozen=True)
class CheckOutcome:
    """Befunde einer Prüfung; `truncated` = Anzahl weiterer, nicht aufgenommener Befunde."""

    findings: list[RawFinding]
    truncated: int = 0


def parse_safely(data: bytes) -> ParsedDocument:
    """Liest XML mit gehärtetem lxml-Parser.

    Raises:
        NotCheckableError: Die Datei ist nicht lesbar oder enthält ein `DOCTYPE`.
    """
    parser = etree.XMLParser(
        resolve_entities=False, no_network=True, load_dtd=False, huge_tree=False
    )
    try:
        document = etree.parse(io.BytesIO(data), parser)
    except etree.XMLSyntaxError as error:
        raise NotCheckableError(str(error)[:_MAX_DETAIL]) from error
    if document.docinfo.doctype or document.docinfo.internalDTD is not None:
        raise NotCheckableError("DOCTYPE")
    return ParsedDocument(document)


def _clean(message: str) -> str:
    return " ".join(message.replace(NETEX_NAMESPACE_PREFIX, "").split())[:_MAX_DETAIL]


class XsdChecker:
    """Prüft Dokumente gegen die XSD; lädt sie erst beim ersten Gebrauch (einmal, threadsicher)."""

    def __init__(self, xsd_path: Path) -> None:
        self._path = xsd_path
        self._lock = threading.Lock()
        self._schema: etree.XMLSchema | None = None
        self._failed = False

    @property
    def loaded(self) -> bool:
        """`True`, sobald die XSD geladen ist."""
        return self._schema is not None

    def load(self) -> etree.XMLSchema:
        """Lädt die XSD bei Bedarf (dauert rund 17 s).

        Raises:
            RulesUnavailableError: Die XSD fehlt oder ist nicht ladbar.
        """
        with self._lock:
            if self._schema is not None:
                return self._schema
            if self._failed or not self._path.is_file():
                raise RulesUnavailableError(self._path.name)
            try:
                parser = etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False)
                self._schema = etree.XMLSchema(etree.parse(str(self._path), parser))
            except (etree.XMLSyntaxError, etree.XMLSchemaParseError, OSError) as error:
                self._failed = True
                logger.warning("XSD nicht ladbar: %s", error)
                raise RulesUnavailableError(self._path.name) from error
            return self._schema

    def check(self, document: ParsedDocument) -> CheckOutcome:
        """Gültigkeit gegen die XSD; Befunde mit Zeile und Originalmeldung."""
        schema = self.load()
        with self._lock:
            schema.validate(cast("etree._ElementTree", document))
            log = list(schema.error_log)
        findings = []
        for entry in log[:MAX_FINDINGS]:
            match = _ELEMENT_IN_MESSAGE.search(entry.message)
            findings.append(
                RawFinding(entry.line, match.group(1) if match else None, _clean(entry.message))
            )
        return CheckOutcome(findings, max(len(log) - MAX_FINDINGS, 0))


class SchematronChecker:
    """Prüft Dokumente gegen Schematron-Regeln (`general_rules.sch`) mit `lxml.isoschematron`."""

    def __init__(self, rules_path: Path) -> None:
        self._path = rules_path
        self._lock = threading.Lock()
        self._schematron: isoschematron.Schematron | None = None
        self._failed = False

    def _load(self) -> isoschematron.Schematron:
        if self._schematron is not None:
            return self._schematron
        if self._failed or not self._path.is_file():
            raise RulesUnavailableError(self._path.name)
        try:
            parser = etree.XMLParser(resolve_entities=False, no_network=True, load_dtd=False)
            self._schematron = isoschematron.Schematron(
                etree.parse(str(self._path), parser), store_report=True
            )
        except (etree.XMLSyntaxError, etree.SchematronParseError, OSError) as error:
            self._failed = True
            logger.warning("Schematron-Regeln nicht ladbar: %s", error)
            raise RulesUnavailableError(self._path.name) from error
        return self._schematron

    def check(self, document: ParsedDocument) -> CheckOutcome:
        """Verstösse gegen die Regeln; `rule` ist die Kennung des Musters (`pattern id`)."""
        with self._lock:
            schematron = self._load()
            schematron.validate(cast("etree._ElementTree", document))
            report = schematron.validation_report
        findings: list[RawFinding] = []
        total = 0
        pattern: str | None = None
        for node in report.getroot():
            if node.tag == f"{_SVRL}active-pattern":
                pattern = node.get("id")
            elif node.tag == f"{_SVRL}failed-assert":
                total += 1
                if len(findings) < MAX_FINDINGS:
                    findings.append(self._finding(document, node, pattern))
        return CheckOutcome(findings, total - len(findings))

    @staticmethod
    def _finding(document: ParsedDocument, node: etree._Element, pattern: str | None) -> RawFinding:
        detail = _clean("".join(node.itertext()))
        location = node.get("location")
        line, name = 1, None
        if location:
            try:
                targets = cast("etree._ElementTree", document).xpath(location)
            except etree.XPathError:
                targets = []
            if isinstance(targets, list) and targets and isinstance(targets[0], etree._Element):
                line = targets[0].sourceline or 1
                name = etree.QName(targets[0]).localname
        return RawFinding(line, name, detail, pattern)
