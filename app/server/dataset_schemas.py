"""Antwortmodelle für Datensätze, Objekte, Fahrten, Diagnosen und XML-Ausschnitte."""

from __future__ import annotations

import re

from pydantic import Field

from app.core.dataset import Dataset
from app.core.diagnostics import DiagnosticCategory
from app.core.explorer import ObjectDetail, PropertyNode, ReferenceView, XmlWindow, editor_text
from app.core.frames import color_key
from app.core.guide.links import GuideLinks, guide_url
from app.core.index.dataset_index import ElementRow, FileSummary, IndexedDiagnostic
from app.core.index.references import ResolveStatus
from app.core.messages import MessageKey, Severity
from app.core.projection.common import Lookup, LookupStatus
from app.core.projection.journeys import JourneySummary
from app.core.provenance import ChainLink, LinkKind
from app.core.validation.detection import (
    DetectionStatus,
    Evidence,
    ProfileVersion,
    VersionDetection,
)
from app.core.validation.result import ValidationSummary
from app.server.datasets import object_id
from app.server.schemas import ApiModel, IssueOut

_CHAPTER_PATH = re.compile(r"^src/[A-Za-z0-9_]+\.md$")


class OpenDatasetIn(ApiModel):
    """Anfrage `POST /api/datasets`: ein Beispiel des Guides über seinen Dateinamen."""

    example: str = Field(min_length=1, max_length=255)


class DetectionReasonOut(ApiModel):
    """Ein Hinweis der Versionserkennung: wofür er spricht, Schlüssel und Parameter."""

    evidence: Evidence
    key: MessageKey
    params: dict[str, str | int]


class DetectionOut(ApiModel):
    """Ergebnis der Versionserkennung einer Datei, mit Begründung."""

    status: DetectionStatus
    profile: ProfileVersion | None
    reasons: list[DetectionReasonOut]

    @classmethod
    def from_detection(cls, detection: VersionDetection) -> DetectionOut:
        """Wandelt das Ergebnis des Kerns um."""
        return cls(
            status=detection.status,
            profile=detection.profile,
            reasons=[
                DetectionReasonOut(evidence=r.evidence, key=r.key, params=dict(r.params))
                for r in detection.reasons
            ],
        )


class FileOut(ApiModel):
    """Eine Datei des Datensatzes."""

    id: int
    name: str
    size: int
    sha256: str
    readable: bool
    elements: int
    objects: int
    detection: DetectionOut | None


class StepOutcomeOut(ApiModel):
    """Prüfschritt der Validierung: durchgeführt oder, mit Grund, nicht durchgeführt."""

    id: str
    performed: bool
    reason: IssueOut | None


class FileOutcomeOut(ApiModel):
    """Datei der Validierung: geprüft oder, mit Grund, nicht geprüft."""

    file_id: int
    checked: bool
    reason: IssueOut | None
    forced: bool


class ValidationOut(ApiModel):
    """Ergebnis einer Validierung: „geprüft gegen Entwurf <Commit>“, nie „gültig“."""

    guide_commit: str | None
    forced: bool
    steps: list[StepOutcomeOut]
    files: list[FileOutcomeOut]

    @classmethod
    def from_summary(cls, summary: ValidationSummary) -> ValidationOut:
        """Wandelt das Ergebnis des Kerns um."""
        return cls(
            guide_commit=summary.guide_commit,
            forced=summary.forced,
            steps=[
                StepOutcomeOut(
                    id=s.step_id,
                    performed=s.performed,
                    reason=None if s.reason is None else IssueOut.from_issue(s.reason),
                )
                for s in summary.steps
            ],
            files=[
                FileOutcomeOut(
                    file_id=f.file_id,
                    checked=f.checked,
                    reason=None if f.reason is None else IssueOut.from_issue(f.reason),
                    forced=f.forced,
                )
                for f in summary.files
            ],
        )


class CountOut(ApiModel):
    """Name mit Anzahl."""

    name: str
    count: int


class FrameRefOut(ApiModel):
    """Frame einer Angabe: Objekt-ID, Typ, `id` aus der Datei."""

    object_id: str
    name: str
    xml_id: str | None


class ObjectOut(ApiModel):
    """Kurzangaben zu einem Objekt oder Element."""

    id: str
    name: str
    xml_id: str | None
    version: str | None
    label: str | None
    file_name: str
    line: int
    column: int
    frame: FrameRefOut | None
    color_key: str | None
    not_relevant: bool


class DatasetOut(ApiModel):
    """Antwort `POST /api/datasets` und `GET /api/datasets/{id}`."""

    id: str
    files: list[FileOut]
    object_types: list[CountOut]
    frames: list[ObjectOut]
    diagnostic_counts: dict[Severity, int]
    validation: ValidationOut | None


class ObjectSearchOut(ApiModel):
    """Antwort der einfachen Objektsuche."""

    total: int
    items: list[ObjectOut]


class PropertyReferenceOut(ApiModel):
    """Status und Ziel einer Referenz im Eigenschaftsbaum."""

    status: ResolveStatus
    target_id: str | None
    expected: list[str]


class PropertyOut(ApiModel):
    """Ein Kindelement im Eigenschaftsbaum (Text unverändert)."""

    id: str
    name: str
    attributes: dict[str, str]
    text: str
    line: int
    column: int
    reference: PropertyReferenceOut | None
    children: list[PropertyOut]


class ReferenceOut(ApiModel):
    """Eine Referenz: Ref-Element, Wert, Status, erwartete Typen, Ziel und enthaltendes Objekt."""

    element: ObjectOut
    ref: str
    ref_version: str | None
    status: ResolveStatus
    expected: list[str]
    target: ObjectOut | None
    owner: ObjectOut | None


class ObjectDetailOut(ApiModel):
    """Antwort `GET /api/objects/{id}`."""

    object: ObjectOut
    path: str
    attributes: dict[str, str]
    properties: list[PropertyOut]
    truncated: bool
    reference: ReferenceOut | None
    outgoing: list[ReferenceOut]
    incoming: list[ReferenceOut]
    references_truncated: bool


class ChainLinkOut(ApiModel):
    """Ein Glied der Herkunftskette."""

    kind: LinkKind
    object: ObjectOut


class LookupOut(ApiModel):
    """Eine Angabe der Fahrtenliste mit Status und Herkunft."""

    status: LookupStatus
    text: str | None
    object_id: str | None


class JourneyOut(ApiModel):
    """Eine Fahrt in der Liste."""

    object: ObjectOut
    train_numbers: list[LookupOut]
    departure_time: LookupOut
    departure_day_offset: LookupOut
    line: LookupOut
    first_stop: LookupOut
    last_stop: LookupOut
    category: LookupOut


class DiagnosticOut(ApiModel):
    """Eine Diagnose mit Stelle."""

    category: DiagnosticCategory
    severity: Severity
    key: MessageKey
    params: dict[str, str | int]
    file_id: int
    file_name: str
    line: int | None
    column: int | None
    guide_link: str | None = None


class FrameBandOut(ApiModel):
    """Zeilenbereich eines Frames im XML-Ausschnitt."""

    object_id: str
    name: str
    xml_id: str | None
    color_key: str | None
    from_line: int
    to_line: int


class XmlWindowOut(ApiModel):
    """XML-Ausschnitt mit markiertem Bereich.

    `text` hat nur LF als Zeilenumbruch; `focus_from`/`focus_to` zählen UTF-16-Einheiten
    (wie im Browser).
    """

    file_name: str
    first_line: int
    text: str
    focus_from: int
    focus_to: int
    frames: list[FrameBandOut]
    truncated: bool


class Converter:
    """Wandelt Ergebnisse des Kerns für einen Datensatz in Antwortmodelle um."""

    def __init__(
        self,
        dataset_id: str,
        dataset: Dataset,
        links: GuideLinks | None = None,
        guide_commit: str | None = None,
    ) -> None:
        self.dataset_id = dataset_id
        self._dataset = dataset
        self.index = dataset.index
        self._links = links or GuideLinks()
        self._guide_commit = guide_commit
        self._frames: dict[int, ElementRow | None] = {}

    def _frame(self, element: ElementRow) -> ElementRow | None:
        if element.frame_id is None:
            return None
        if element.frame_id not in self._frames:
            self._frames[element.frame_id] = self.index.element(element.frame_id)
        return self._frames[element.frame_id]

    def object(self, element: ElementRow) -> ObjectOut:
        """Kurzangaben zu einem Element."""
        frame = self._frame(element)
        frame_ref = (
            None
            if frame is None
            else FrameRefOut(
                object_id=object_id(self.dataset_id, frame.id), name=frame.name, xml_id=frame.xml_id
            )
        )
        return ObjectOut(
            id=object_id(self.dataset_id, element.id),
            name=element.name,
            xml_id=element.xml_id,
            version=element.version,
            label=element.label,
            file_name=element.file_name,
            line=element.start.line,
            column=element.start.column,
            frame=frame_ref,
            color_key=color_key(element, frame),
            not_relevant=element.not_relevant,
        )

    def dataset(self) -> DatasetOut:
        """Übersicht über den Datensatz."""
        counts = dict.fromkeys(Severity, 0)
        for item in self.index.diagnostics():
            counts[item.diagnostic.severity] += 1
        return DatasetOut(
            id=self.dataset_id,
            files=[self._file(summary) for summary in self.index.files()],
            object_types=[CountOut(name=n, count=c) for n, c in self.index.object_types()],
            frames=[self.object(frame) for frame in self.index.frames()],
            diagnostic_counts=counts,
            validation=None
            if self._dataset.validation is None
            else ValidationOut.from_summary(self._dataset.validation),
        )

    def _file(self, summary: FileSummary) -> FileOut:
        detection = self._dataset.detections.get(summary.id)
        return FileOut(
            **vars(summary),
            detection=None if detection is None else DetectionOut.from_detection(detection),
        )

    def reference(self, view: ReferenceView) -> ReferenceOut:
        """Eine Referenz mit Ziel und enthaltendem Objekt."""
        row = view.row
        return ReferenceOut(
            element=self.object(view.element),
            ref=row.target_ref,
            ref_version=row.ref_version,
            status=row.status,
            expected=list(row.expected),
            target=None if view.target is None else self.object(view.target),
            owner=None if view.owner is None else self.object(view.owner),
        )

    def _property(self, node: PropertyNode) -> PropertyOut:
        element = node.element
        view = node.reference
        reference = (
            None
            if view is None
            else PropertyReferenceOut(
                status=view.row.status,
                target_id=None
                if view.target is None
                else object_id(self.dataset_id, view.target.id),
                expected=list(view.row.expected),
            )
        )
        return PropertyOut(
            id=object_id(self.dataset_id, element.id),
            name=element.name,
            attributes=element.attributes,
            text=element.text,
            line=element.start.line,
            column=element.start.column,
            reference=reference,
            children=[self._property(child) for child in node.children],
        )

    def detail(self, detail: ObjectDetail) -> ObjectDetailOut:
        """Objektdetail."""
        return ObjectDetailOut(
            object=self.object(detail.element),
            path=detail.path,
            attributes=detail.element.attributes,
            properties=[self._property(node) for node in detail.properties],
            truncated=detail.truncated,
            reference=None if detail.reference is None else self.reference(detail.reference),
            outgoing=[self.reference(view) for view in detail.outgoing],
            incoming=[self.reference(view) for view in detail.incoming],
            references_truncated=detail.references_truncated,
        )

    def chain(self, links: list[ChainLink]) -> list[ChainLinkOut]:
        """Herkunftskette."""
        return [ChainLinkOut(kind=link.kind, object=self.object(link.element)) for link in links]

    def _lookup(self, lookup: Lookup) -> LookupOut:
        element = lookup.element
        return LookupOut(
            status=lookup.status,
            text=lookup.text,
            object_id=None if element is None else object_id(self.dataset_id, element.id),
        )

    def journey(self, journey: JourneySummary) -> JourneyOut:
        """Eine Fahrt der Liste."""
        return JourneyOut(
            object=self.object(journey.element),
            train_numbers=[self._lookup(number) for number in journey.train_numbers],
            departure_time=self._lookup(journey.departure_time),
            departure_day_offset=self._lookup(journey.departure_day_offset),
            line=self._lookup(journey.line),
            first_stop=self._lookup(journey.first_stop),
            last_stop=self._lookup(journey.last_stop),
            category=self._lookup(journey.category),
        )

    def _chapter(self, params: dict[str, str | int]) -> str | None:
        """Kapitel einer Diagnose: das genannte, sonst das erste im Index zum Element."""
        named = params.get("chapter")
        if isinstance(named, str) and _CHAPTER_PATH.match(named):
            return named
        element = params.get("element")
        return self._links.chapter(element) if isinstance(element, str) else None

    def diagnostic(self, item: IndexedDiagnostic) -> DiagnosticOut:
        """Eine Diagnose, bei Elementbezug mit Verweis auf das Guide-Kapitel."""
        diagnostic = item.diagnostic
        position = diagnostic.position
        chapter = self._chapter(diagnostic.params)
        return DiagnosticOut(
            category=diagnostic.category,
            severity=diagnostic.severity,
            key=diagnostic.key,
            params=dict(diagnostic.params),
            file_id=item.file_id,
            file_name=item.file_name,
            line=None if position is None else position.line,
            column=None if position is None else position.column,
            guide_link=guide_url(self._guide_commit, chapter),
        )

    def xml_window(self, window: XmlWindow) -> XmlWindowOut:
        """XML-Ausschnitt mit Frame-Bereichen."""
        text, focus_from, focus_to = editor_text(window)
        return XmlWindowOut(
            file_name=window.file_name,
            first_line=window.first_line,
            text=text,
            focus_from=focus_from,
            focus_to=focus_to,
            frames=[
                FrameBandOut(
                    object_id=object_id(self.dataset_id, band.frame.id),
                    name=band.frame.name,
                    xml_id=band.frame.xml_id,
                    color_key=color_key(band.frame, band.frame),
                    from_line=band.from_line,
                    to_line=band.to_line,
                )
                for band in window.frames
            ],
            truncated=window.truncated,
        )
