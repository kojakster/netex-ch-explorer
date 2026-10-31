"""Antwortmodelle der lokalen JSON-Schnittstelle (Vertrag: docs/api.md)."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel

from app.core.config import AppConfig
from app.core.features import Feature
from app.core.guide.examples import ExampleResult
from app.core.guide.status import ExampleChange, ExampleStatus, GuideStatus, GuideTestState
from app.core.messages import Issue, MessageKey, Severity
from app.core.validation.core_rules import CORE_RULES, RuleKind
from app.core.validation.steps import CHECK_STEPS, CheckStatus


class ApiModel(BaseModel):
    """Basis aller Antworten: Feldnamen in camelCase, unveränderlich."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True, frozen=True)


class IssueOut(ApiModel):
    """Meldung als Übersetzungsschlüssel mit Parametern."""

    severity: Severity
    key: MessageKey
    params: dict[str, str | int]

    @classmethod
    def from_issue(cls, issue: Issue) -> IssueOut:
        """Wandelt eine Meldung des Kerns um."""
        return cls(severity=issue.severity, key=issue.key, params=dict(issue.params))


class MappingSheetOut(ApiModel):
    """Zusammenfassung eines gelesenen Blatts der Mappingtabelle."""

    name: str
    header_row: int
    rows: int


class ExampleOut(ApiModel):
    """Ein Beispiel des Guides mit Ergebnis und Stand gegenüber dem letzten Test."""

    name: str
    title: str | None
    result: ExampleResult | None
    counts: dict[Severity, int]
    change: ExampleChange

    @classmethod
    def from_status(cls, status: ExampleStatus) -> ExampleOut:
        """Wandelt den Beispielstatus des Kerns um."""
        return cls(
            name=status.name,
            title=status.title,
            result=status.result,
            counts=dict(status.counts),
            change=status.change,
        )


class GuideOut(ApiModel):
    """Antwort von `GET /api/guide`."""

    path: str
    found: bool
    branch: str | None
    commit: str | None
    xsd_commit: str | None
    xsd_present: bool
    test_state: GuideTestState
    tested_commit: str | None
    mapping_sheets: list[MappingSheetOut]
    examples: list[ExampleOut]
    examples_ready: bool
    xsd_loaded: bool
    issues: list[IssueOut]

    @classmethod
    def from_status(cls, status: GuideStatus, *, xsd_loaded: bool) -> GuideOut:
        """Wandelt den Guide-Status des Kerns um.

        `xsd_loaded`: Die XSD ist geladen; bis dahin läuft die Prüfung der Beispiele im Hintergrund.
        """
        return cls(
            path=str(status.path),
            found=status.found,
            branch=status.revision.branch,
            commit=status.revision.commit,
            xsd_commit=status.revision.xsd_commit,
            xsd_present=status.xsd_present,
            test_state=status.test_state,
            tested_commit=status.tested_commit,
            mapping_sheets=[
                MappingSheetOut(name=sheet.name, header_row=sheet.header_row, rows=len(sheet.rows))
                for sheet in status.mapping.sheets.values()
            ],
            examples=[ExampleOut.from_status(example) for example in status.examples],
            examples_ready=status.examples_ready,
            xsd_loaded=xsd_loaded,
            issues=[IssueOut.from_issue(issue) for issue in status.issues],
        )


class FrameColorOut(ApiModel):
    """Farbe einer Frame-Markierung."""

    key: str
    background: str
    text: str


class CheckStepOut(ApiModel):
    """Prüfschritt für die Hilfeseite."""

    id: str
    status: CheckStatus
    sources: list[str]


class CoreRuleOut(ApiModel):
    """Kernregel für die Hilfeseite: Kennung, Art, Pfad, Schweregrad und Quelle."""

    id: str
    kind: RuleKind
    severity: Severity
    context: str
    targets: list[str]
    source: str
    allowed: list[str]


class AppInfoOut(ApiModel):
    """Antwort von `GET /api/app`: Daten für Legende, Hilfeseite und Sprache."""

    language: str
    languages: list[str]
    frame_colors: list[FrameColorOut]
    not_relevant_elements: list[str]
    features: list[Feature]
    checks: list[CheckStepOut]
    core_rules: list[CoreRuleOut]
    severities: list[Severity]
    issues: list[IssueOut]

    @classmethod
    def from_config(cls, config: AppConfig, languages: tuple[str, ...]) -> AppInfoOut:
        """Stellt die Antwort aus Einstellungen und den Listen des Kerns zusammen."""
        return cls(
            language=config.settings.language,
            languages=list(languages),
            frame_colors=[
                FrameColorOut(key=key, background=color.background, text=color.text)
                for key, color in config.frame_colors.items()
            ],
            not_relevant_elements=list(config.not_relevant_elements),
            features=list(Feature),
            checks=[
                CheckStepOut(id=step.id, status=step.status, sources=list(step.sources))
                for step in CHECK_STEPS
            ],
            core_rules=[
                CoreRuleOut(
                    id=rule.id,
                    kind=rule.kind,
                    severity=rule.severity,
                    context=rule.context,
                    targets=["/".join(path) for path in rule.targets],
                    source=rule.source,
                    allowed=list(rule.allowed),
                )
                for rule in CORE_RULES
            ],
            severities=list(Severity),
            issues=[IssueOut.from_issue(issue) for issue in config.issues],
        )
