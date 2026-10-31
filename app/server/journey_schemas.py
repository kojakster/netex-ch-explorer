"""Antwortmodelle der Fahrtansicht (`GET /api/journeys/{id}`, Vertrag: docs/api.md)."""

from __future__ import annotations

from pydantic import Field

from app.core.diagnostics import DiagnosticCategory
from app.core.index.dataset_index import ElementRow
from app.core.messages import MessageKey, ParamValue, Severity
from app.core.projection.calendar import OperatingDays, Validity
from app.core.projection.clock import split_seconds
from app.core.projection.common import Finding, LangText, Lookup, LookupStatus
from app.core.projection.journey_view import (
    JourneyView,
    PartBoundary,
    PartTime,
    PartView,
    PrivateCodeView,
    StopView,
)
from app.core.projection.master_data import MasterInfo, MasterStatus
from app.core.projection.notices import NoticeScope, NoticeText, NoticeView
from app.core.projection.offers import (
    CategoryView,
    CodedValue,
    FacilityGroup,
    FacilitySetView,
    TransportView,
)
from app.core.projection.timing import (
    CalcStep,
    OffsetOrigin,
    StepKind,
    TimeResult,
    TimeStatus,
)
from app.server.dataset_schemas import Converter, DiagnosticOut, ObjectOut
from app.server.schemas import ApiModel


class ValueOut(ApiModel):
    """Eine Angabe mit Status, Text aus der Datei und Element der Quelle."""

    status: LookupStatus
    text: str | None
    element: ObjectOut | None


class LangTextOut(ApiModel):
    """Ein Text mit Sprachkennzeichen, unverändert."""

    lang: str | None
    text: str
    element: ObjectOut


class LabelledTextOut(ApiModel):
    """Wert einer Spalte der Mappingtabelle mit dem Spaltennamen."""

    label: str
    text: str


class MasterMatchOut(ApiModel):
    """Eine Zeile der Mappingtabelle: Blatt, Excel-Zeile und Werte."""

    sheet: str
    row: int
    texts: list[LabelledTextOut]


class MasterOut(ApiModel):
    """Bedeutung eines Codes aus den Stammdaten."""

    status: MasterStatus
    matches: list[MasterMatchOut]


class CodeOut(ApiModel):
    """Ein Code aus der Datei mit Quelle und Stammdaten (`null`: keine vorgesehen)."""

    code: str
    element: ObjectOut
    master: MasterOut | None


class FindingOut(ApiModel):
    """Grund oder Hinweis als Übersetzungsschlüssel mit Parametern und Stelle."""

    severity: Severity
    key: MessageKey
    params: dict[str, ParamValue]
    element: ObjectOut | None


class StepOut(ApiModel):
    """Ein Summand der Rechenkette mit Quelle und Zwischenstand."""

    kind: StepKind
    value: str | None
    default: bool
    seconds: int
    clock: str
    day_offset: int
    element: ObjectOut | None
    related: list[ObjectOut]
    via_from_to: bool


class TimeOut(ApiModel):
    """Eine Zeit an einem Halt; `clock` ist `hh:mm:ss`, `dayOffset` der Tag ab Betriebstag."""

    id: str
    status: TimeStatus
    clock: str | None
    day_offset: int
    offset_origin: OffsetOrigin | None
    source: ObjectOut | None
    chain: list[StepOut]
    reason: FindingOut | None


class StopOut(ApiModel):
    """Ein Halt der Fahrt."""

    position: int
    point: ObjectOut
    stop_point: ValueOut
    stop_place: ValueOut
    quay: ValueOut
    assignment: ObjectOut | None
    for_boarding: ValueOut
    for_alighting: ValueOut
    request_stop: ValueOut
    stop_use: CodeOut | None
    arrival: TimeOut | None
    departure: TimeOut | None
    part_numbers: list[int]


class OperatingDaysOut(ApiModel):
    """Betriebstage einer `AvailabilityCondition`."""

    condition: ObjectOut
    from_date: ObjectOut | None
    to_date: ObjectOut | None
    valid_day_bits: ObjectOut | None
    first_day: str | None
    last_day: str | None
    period_days: int | None
    valid_count: int | None
    days: list[str]
    days_listed: bool
    findings: list[FindingOut]


class ValidityOut(ApiModel):
    """Eine `AvailabilityConditionRef` mit Betriebstagen oder dem Grund, warum nicht."""

    ref: ObjectOut
    days: OperatingDaysOut | None
    problem: ValueOut | None


class FacilityGroupOut(ApiModel):
    """Eine Gruppe von Angebots-Codes."""

    element: ObjectOut
    codes: list[CodeOut]


class FacilitySetOut(ApiModel):
    """Ein `ServiceFacilitySet` hinter einer Referenz."""

    ref: ObjectOut
    facility_set: ObjectOut | None
    problem: ValueOut | None
    description: list[LangTextOut]
    groups: list[FacilityGroupOut]


class TransportOut(ApiModel):
    """Verkehrsmittel einer Fahrt oder Linie."""

    owner: ObjectOut
    role: str
    mode: ValueOut
    submode_type: str | None
    submode: ValueOut


class CategoryOut(ApiModel):
    """`TypeOfProductCategory` mit Name aus der Datei und Stammdaten."""

    role: str
    ref: ObjectOut
    target: ObjectOut | None
    problem: ValueOut | None
    short_name: ValueOut
    names: list[LangTextOut]
    master: MasterOut | None


class PartTimeOut(ApiModel):
    """`StartTime`/`EndTime` einer Teilstrecke."""

    time: ValueOut
    day_offset: ValueOut
    clock: str | None
    day: int | None


class PartBoundaryOut(ApiModel):
    """Anfang oder Ende einer Teilstrecke."""

    stop: ValueOut
    position: int | None


class PartOut(ApiModel):
    """Eine `JourneyPart`."""

    number: int
    element: ObjectOut
    description: list[LangTextOut]
    purpose: ValueOut
    train_numbers: list[ValueOut]
    parent_journey: ValueOut
    start_stop: PartBoundaryOut
    end_stop: PartBoundaryOut
    start: PartTimeOut
    end: PartTimeOut
    facilities: list[FacilitySetOut]
    validity: list[ValidityOut]
    category: CategoryOut | None


class NoticeTextOut(ApiModel):
    """Ein Text eines Hinweises, unverändert."""

    text: LangTextOut
    alternative_for: str | None


class NoticeOut(ApiModel):
    """Eine Hinweiszuweisung mit Hinweis und Geltungsbereich."""

    assignment: ObjectOut
    scope: NoticeScope
    ref: ObjectOut | None
    notice: ObjectOut | None
    problem: ValueOut | None
    short_code: ValueOut
    notice_type: ValueOut
    texts: list[NoticeTextOut]
    start_ref: ObjectOut | None
    end_ref: ObjectOut | None
    start_position: int | None
    end_position: int | None
    validity: list[ValidityOut]


class PrivateCodeOut(ApiModel):
    """Ein `PrivateCode` der Fahrt."""

    code_type: str | None
    value: str
    element: ObjectOut


class JourneyViewOut(ApiModel):
    """Antwort `GET /api/journeys/{id}`."""

    journey: ObjectOut
    guide_commit: str | None
    pattern: ValueOut
    time_demand_type: ValueOut
    train_numbers: list[ValueOut]
    private_codes: list[PrivateCodeOut]
    line: ValueOut
    transports: list[TransportOut]
    categories: list[CategoryOut]
    validities: list[ValidityOut]
    stops: list[StopOut]
    parts: list[PartOut]
    facilities: list[FacilitySetOut]
    notices: list[NoticeOut]
    diagnostics: list[DiagnosticOut] = Field(default_factory=list)


class JourneyConverter:
    """Wandelt die Fahrtansicht des Kerns in Antwortmodelle um."""

    def __init__(self, converter: Converter, guide_commit: str | None) -> None:
        self._converter = converter
        self._guide_commit = guide_commit

    def _object(self, element: ElementRow) -> ObjectOut:
        return self._converter.object(element)

    def _optional(self, element: ElementRow | None) -> ObjectOut | None:
        return None if element is None else self._object(element)

    def value(self, lookup: Lookup) -> ValueOut:
        """Eine Angabe."""
        return ValueOut(
            status=lookup.status, text=lookup.text, element=self._optional(lookup.element)
        )

    def _optional_value(self, lookup: Lookup | None) -> ValueOut | None:
        return None if lookup is None else self.value(lookup)

    def _lang(self, text: LangText) -> LangTextOut:
        return LangTextOut(lang=text.lang, text=text.text, element=self._object(text.element))

    def _master(self, master: MasterInfo | None) -> MasterOut | None:
        if master is None:
            return None
        return MasterOut(
            status=master.status,
            matches=[
                MasterMatchOut(
                    sheet=match.sheet,
                    row=match.row,
                    texts=[LabelledTextOut(label=label, text=text) for label, text in match.texts],
                )
                for match in master.matches
            ],
        )

    def _code(self, coded: CodedValue | None) -> CodeOut | None:
        if coded is None:
            return None
        return CodeOut(
            code=coded.code, element=self._object(coded.element), master=self._master(coded.master)
        )

    def _finding(self, finding: Finding | None) -> FindingOut | None:
        if finding is None:
            return None
        return FindingOut(
            severity=finding.severity,
            key=finding.key,
            params=dict(finding.params),
            element=self._optional(finding.element),
        )

    def _step(self, step: CalcStep) -> StepOut:
        day, clock = split_seconds(step.total)
        return StepOut(
            kind=step.kind,
            value=step.value,
            default=step.default,
            seconds=step.seconds,
            clock=clock,
            day_offset=day,
            element=self._optional(step.element),
            related=[self._object(item) for item in step.related],
            via_from_to=step.via_from_to,
        )

    def _time(self, time: TimeResult | None) -> TimeOut | None:
        if time is None:
            return None
        day, clock = (0, None) if time.total is None else split_seconds(time.total)
        return TimeOut(
            id=time.id,
            status=time.status,
            clock=clock,
            day_offset=day,
            offset_origin=time.offset_origin,
            source=self._optional(time.source),
            chain=[self._step(step) for step in time.chain],
            reason=self._finding(time.reason),
        )

    def _stop(self, stop: StopView) -> StopOut:
        return StopOut(
            position=stop.position,
            point=self._object(stop.point),
            stop_point=self.value(stop.stop_point),
            stop_place=self.value(stop.stop_place),
            quay=self.value(stop.quay),
            assignment=self._optional(stop.assignment),
            for_boarding=self.value(stop.for_boarding),
            for_alighting=self.value(stop.for_alighting),
            request_stop=self.value(stop.request_stop),
            stop_use=self._code(stop.stop_use),
            arrival=self._time(stop.times.arrival),
            departure=self._time(stop.times.departure),
            part_numbers=list(stop.part_numbers),
        )

    def _days(self, days: OperatingDays) -> OperatingDaysOut:
        return OperatingDaysOut(
            condition=self._object(days.condition),
            from_date=self._optional(days.from_date),
            to_date=self._optional(days.to_date),
            valid_day_bits=self._optional(days.valid_day_bits),
            first_day=None if days.first_day is None else days.first_day.isoformat(),
            last_day=None if days.last_day is None else days.last_day.isoformat(),
            period_days=days.period_days,
            valid_count=days.valid_count,
            days=[day.isoformat() for day in days.days],
            days_listed=days.days_listed,
            findings=[item for f in days.findings if (item := self._finding(f)) is not None],
        )

    def _validity(self, validity: Validity) -> ValidityOut:
        return ValidityOut(
            ref=self._object(validity.ref),
            days=None if validity.days is None else self._days(validity.days),
            problem=self._optional_value(validity.problem),
        )

    def _facility_group(self, group: FacilityGroup) -> FacilityGroupOut:
        return FacilityGroupOut(
            element=self._object(group.element),
            codes=[item for c in group.codes if (item := self._code(c)) is not None],
        )

    def _facility_set(self, view: FacilitySetView) -> FacilitySetOut:
        return FacilitySetOut(
            ref=self._object(view.ref),
            facility_set=self._optional(view.facility_set),
            problem=self._optional_value(view.problem),
            description=[self._lang(text) for text in view.description],
            groups=[self._facility_group(group) for group in view.groups],
        )

    def _transport(self, view: TransportView) -> TransportOut:
        return TransportOut(
            owner=self._object(view.owner),
            role=view.role,
            mode=self.value(view.mode),
            submode_type=view.submode_type,
            submode=self.value(view.submode),
        )

    def _category(self, view: CategoryView | None) -> CategoryOut | None:
        if view is None:
            return None
        return CategoryOut(
            role=view.role,
            ref=self._object(view.ref),
            target=self._optional(view.target),
            problem=self._optional_value(view.problem),
            short_name=self.value(view.short_name),
            names=[self._lang(name) for name in view.names],
            master=self._master(view.master),
        )

    def _part_time(self, time: PartTime) -> PartTimeOut:
        day, clock = (None, None) if time.total is None else split_seconds(time.total)
        return PartTimeOut(
            time=self.value(time.time),
            day_offset=self.value(time.day_offset),
            clock=clock,
            day=day,
        )

    def _boundary(self, boundary: PartBoundary) -> PartBoundaryOut:
        return PartBoundaryOut(stop=self.value(boundary.stop), position=boundary.position)

    def _part(self, part: PartView) -> PartOut:
        return PartOut(
            number=part.number,
            element=self._object(part.element),
            description=[self._lang(text) for text in part.description],
            purpose=self.value(part.purpose),
            train_numbers=[self.value(number) for number in part.train_numbers],
            parent_journey=self.value(part.parent_journey),
            start_stop=self._boundary(part.start_stop),
            end_stop=self._boundary(part.end_stop),
            start=self._part_time(part.start),
            end=self._part_time(part.end),
            facilities=[self._facility_set(view) for view in part.facilities],
            validity=[self._validity(view) for view in part.validity],
            category=self._category(part.category),
        )

    def _notice_text(self, text: NoticeText) -> NoticeTextOut:
        return NoticeTextOut(text=self._lang(text.text), alternative_for=text.alternative_for)

    def _notice(self, notice: NoticeView) -> NoticeOut:
        return NoticeOut(
            assignment=self._object(notice.assignment),
            scope=notice.scope,
            ref=self._optional(notice.ref),
            notice=self._optional(notice.notice),
            problem=self._optional_value(notice.problem),
            short_code=self.value(notice.short_code),
            notice_type=self.value(notice.notice_type),
            texts=[self._notice_text(text) for text in notice.texts],
            start_ref=self._optional(notice.start_ref),
            end_ref=self._optional(notice.end_ref),
            start_position=notice.start_position,
            end_position=notice.end_position,
            validity=[self._validity(view) for view in notice.validity],
        )

    def _private_code(self, code: PrivateCodeView) -> PrivateCodeOut:
        return PrivateCodeOut(
            code_type=code.code_type, value=code.value, element=self._object(code.element)
        )

    def _diagnostic(self, finding: Finding, fallback: ElementRow) -> DiagnosticOut:
        element = finding.element or fallback
        located = finding.element is not None
        return DiagnosticOut(
            category=DiagnosticCategory.PROJECTION,
            severity=finding.severity,
            key=finding.key,
            params=dict(finding.params),
            file_id=element.file_id,
            file_name=element.file_name,
            line=element.start.line if located else None,
            column=element.start.column if located else None,
        )

    def journey(self, view: JourneyView) -> JourneyViewOut:
        """Die ganze Fahrtansicht."""
        return JourneyViewOut(
            journey=self._object(view.journey),
            guide_commit=self._guide_commit,
            pattern=self.value(view.pattern),
            time_demand_type=self.value(view.time_demand_type),
            train_numbers=[self.value(number) for number in view.train_numbers],
            private_codes=[self._private_code(code) for code in view.private_codes],
            line=self.value(view.line),
            transports=[self._transport(item) for item in view.transports],
            categories=[item for c in view.categories if (item := self._category(c)) is not None],
            validities=[self._validity(item) for item in view.validities],
            stops=[self._stop(stop) for stop in view.stops],
            parts=[self._part(part) for part in view.parts],
            facilities=[self._facility_set(item) for item in view.facilities],
            notices=[self._notice(item) for item in view.notices],
            diagnostics=[self._diagnostic(f, view.journey) for f in view.findings],
        )
