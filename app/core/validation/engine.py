"""Validierung eines Datensatzes: XSD, `general_rules.sch` und Schweizer Kernregeln.

Ablauf (docs/decisions.md, „Eigene Dateien prüfen“): zuerst die Version erkennen, dann prüfen.
Nur Dateien, die als CH 2.0 erkannt sind, werden gegen den Guide-Stand geprüft; andere Dateien
bleiben im generischen Explorer nutzbar, erhalten aber keine irreführende 2.0-Prüfung.

Das Ergebnis heisst „geprüft gegen Entwurf <Commit>“, nie „gültig“. Befunde werden als Diagnosen
der Arten `xsd` und `profile_rule` im Index des Datensatzes abgelegt; eine erneute Validierung
ersetzt sie.
"""

from __future__ import annotations

import logging
from pathlib import Path
from typing import Final

from app.core.dataset import Dataset
from app.core.diagnostics import Diagnostic, DiagnosticCategory
from app.core.guide.layout import CHAPTER_XML_MODELLING, GENERAL_RULES_FILE, XSD_MAIN_FILE
from app.core.messages import Issue, MessageKey, Severity
from app.core.validation.core_rules import STEP_ID as CORE_STEP
from app.core.validation.core_rules import check_core_rules
from app.core.validation.lxml_checks import (
    CheckOutcome,
    NotCheckableError,
    ParsedDocument,
    RawFinding,
    RulesUnavailableError,
    SchematronChecker,
    XsdChecker,
    parse_safely,
)
from app.core.validation.result import FileOutcome, StepOutcome, ValidationSummary

logger = logging.getLogger(__name__)

XSD_STEP: Final = "xsd"
GENERAL_STEP: Final = "general_rules"
_PATTERN_KEYS: Final = {
    "no_version_any": MessageKey.SCHEMATRON_NO_VERSION_ANY,
    "no_versionRef_any": MessageKey.SCHEMATRON_NO_VERSIONREF_ANY,
    "ref_elements_require_version": MessageKey.SCHEMATRON_REF_REQUIRES_VERSION,
    "no_order_attribute": MessageKey.SCHEMATRON_NO_ORDER_ATTRIBUTE,
}
_RESULT_CATEGORIES: Final = (DiagnosticCategory.XSD, DiagnosticCategory.PROFILE_RULE)


class ValidationEngine:
    """Hält die geladene XSD und die Schematron-Regeln und prüft Datensätze damit."""

    def __init__(self, guide_path: Path, guide_commit: str | None) -> None:
        self.guide_commit = guide_commit
        self._xsd = XsdChecker(guide_path.joinpath(*XSD_MAIN_FILE.parts))
        self._schematron = SchematronChecker(guide_path.joinpath(*GENERAL_RULES_FILE.parts))

    @property
    def xsd_loaded(self) -> bool:
        """`True`, sobald die XSD geladen ist (Laden dauert rund 17 s)."""
        return self._xsd.loaded

    def preload(self) -> bool:
        """Lädt die XSD jetzt (für den Hintergrund beim Start); `False`, wenn sie fehlt."""
        try:
            self._xsd.load()
        except RulesUnavailableError:
            return False
        return True

    def validate(self, dataset: Dataset) -> ValidationSummary:
        """Prüft alle Dateien des Datensatzes, die als CH 2.0 erkannt sind."""
        with dataset.validation_lock:
            summary = self._validate(dataset)
            dataset.validation = summary
        return summary

    def _validate(self, dataset: Dataset) -> ValidationSummary:
        index = dataset.index
        index.clear_diagnostics(_RESULT_CATEGORIES)
        files: list[FileOutcome] = []
        checkable: list[int] = []
        for summary in index.files():
            detection = dataset.detections.get(summary.id)
            if not summary.readable or detection is None:
                reason = Issue(Severity.INFO, MessageKey.VALIDATION_FILE_SKIPPED_UNREADABLE)
                files.append(FileOutcome(summary.id, False, reason))
            elif not detection.checkable:
                reason = Issue(
                    Severity.INFO,
                    MessageKey.VALIDATION_FILE_SKIPPED_PROFILE,
                    {"status": detection.status, "profile": detection.profile or ""},
                )
                files.append(FileOutcome(summary.id, False, reason))
            else:
                files.append(FileOutcome(summary.id, True))
                checkable.append(summary.id)
        steps = self._run_lxml_steps(dataset, checkable)
        findings = check_core_rules(index, frozenset(checkable))
        for finding in findings:
            index.add_diagnostics(finding.file_id, [finding.diagnostic])
        steps.append(StepOutcome(CORE_STEP, performed=True))
        return ValidationSummary(self.guide_commit, tuple(steps), tuple(files))

    def _run_lxml_steps(self, dataset: Dataset, file_ids: list[int]) -> list[StepOutcome]:
        unavailable: dict[str, Issue] = {}
        for file_id in file_ids:
            document = self._parse(dataset, file_id)
            if document is None:
                continue
            for step, checker in ((XSD_STEP, self._xsd), (GENERAL_STEP, self._schematron)):
                if step in unavailable:
                    continue
                try:
                    outcome = checker.check(document)
                except RulesUnavailableError:
                    unavailable[step] = Issue(
                        Severity.WARNING, MessageKey.VALIDATION_STEP_UNAVAILABLE, {"step": step}
                    )
                    continue
                self._store(dataset, file_id, step, outcome)
        return [
            StepOutcome(step, step not in unavailable, unavailable.get(step))
            for step in (XSD_STEP, GENERAL_STEP)
        ]

    def _parse(self, dataset: Dataset, file_id: int) -> ParsedDocument | None:
        data = dataset.file_data.get(file_id)
        if data is None:
            return None
        try:
            return parse_safely(data)
        except NotCheckableError as error:
            diagnostic = Diagnostic(
                DiagnosticCategory.XSD,
                Severity.ERROR,
                MessageKey.XSD_UNCHECKABLE,
                {"detail": str(error)},
            )
            dataset.index.add_diagnostics(file_id, [diagnostic])
            return None

    def _store(self, dataset: Dataset, file_id: int, step: str, outcome: CheckOutcome) -> None:
        diagnostics = [self._diagnostic(dataset, file_id, step, f) for f in outcome.findings]
        if outcome.truncated:
            diagnostics.append(
                Diagnostic(
                    DiagnosticCategory.XSD if step == XSD_STEP else DiagnosticCategory.PROFILE_RULE,
                    Severity.INFO,
                    MessageKey.VALIDATION_TRUNCATED,
                    {"step": step, "count": outcome.truncated},
                )
            )
        dataset.index.add_diagnostics(file_id, diagnostics)

    @staticmethod
    def _diagnostic(dataset: Dataset, file_id: int, step: str, finding: RawFinding) -> Diagnostic:
        position = dataset.index.position_at(file_id, max(finding.line, 1), skip_indent=True)
        params: dict[str, str | int] = {"step": step, "element": finding.element or ""}
        if step == XSD_STEP:
            params["detail"] = finding.detail
            return Diagnostic(
                DiagnosticCategory.XSD, Severity.ERROR, MessageKey.XSD_VIOLATION, params, position
            )
        pattern = finding.rule or ""
        params["rule"] = f"{GENERAL_STEP}.{pattern}"
        # Versionen und Reihenfolge der Elemente beschreibt das Kapitel zur XML-Modellierung.
        params["chapter"] = str(CHAPTER_XML_MODELLING)
        key = _PATTERN_KEYS.get(pattern)
        if key is None:
            key = MessageKey.SCHEMATRON_VIOLATION
            params["detail"] = finding.detail
        return Diagnostic(DiagnosticCategory.PROFILE_RULE, Severity.ERROR, key, params, position)
