"""Hinweise (`NoticeAssignment` → `Notice`) einer Fahrt.

Belege in docs/mapping.md: N1 bis N5. Eine `NoticeAssignment` gehört zur Fahrt, wenn sie

- in der `ServiceJourney` (`noticeAssignments`) steht,
- im `ServiceJourneyPattern` der Fahrt oder in einem seiner `StopPointInJourneyPattern` steht,
- auf Frame-Ebene steht und die Fahrt (`ServiceJourneyRef`, `NoticedObjectRef`) oder ihr
  `ServiceJourneyPattern` (`JourneyPatternRef`) nennt.

Eine `NoticeAssignment` auf Frame-Ebene ohne jeden Verweis auf ein Objekt (Beispiel 08) gehört zu
keiner bestimmten Fahrt; die Fahrtansicht zeigt sie nicht und meldet die Anzahl als Hinweis.
Texte erscheinen unverändert in allen Sprachen.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import StrEnum
from typing import Final

from app.core.index.dataset_index import DatasetIndex, ElementRow
from app.core.projection.calendar import Validity, validities
from app.core.projection.common import (
    LangText,
    Lookup,
    LookupStatus,
    child,
    children,
    follow,
    multilingual,
    text_of,
)

_OBJECT_REFS: Final = frozenset({"ServiceJourneyRef", "JourneyPatternRef", "NoticedObjectRef"})


class NoticeScope(StrEnum):
    """Wodurch die Hinweiszuweisung zur Fahrt gehört."""

    JOURNEY = "journey"
    """In der `ServiceJourney` eingebettet."""
    PATTERN = "pattern"
    """Im `ServiceJourneyPattern` der Fahrt eingebettet."""
    JOURNEY_REF = "journey_ref"
    """Auf Frame-Ebene, mit `ServiceJourneyRef` oder `NoticedObjectRef` auf die Fahrt."""
    PATTERN_REF = "pattern_ref"
    """Auf Frame-Ebene, mit `JourneyPatternRef` auf das Fahrtmuster der Fahrt."""
    STOP = "stop"
    """In einem `StopPointInJourneyPattern` des Fahrtmusters eingebettet (gilt für diesen Halt)."""


@dataclass(frozen=True)
class NoticeText:
    """Ein Text eines Hinweises; `alternative_for` nennt das Ziel einer `AlternativeText`."""

    text: LangText
    alternative_for: str | None = None


@dataclass(frozen=True)
class NoticeView:
    """Eine Hinweiszuweisung mit Hinweis, Texten und Geltungsbereich."""

    assignment: ElementRow
    scope: NoticeScope
    ref: ElementRow | None
    notice: ElementRow | None
    problem: Lookup | None
    short_code: Lookup
    notice_type: Lookup
    texts: list[NoticeText]
    start_ref: ElementRow | None
    end_ref: ElementRow | None
    start_position: int | None
    """Position des ersten Halts in dieser Fahrt (ab 1); `None`, wenn nicht genannt."""
    end_position: int | None
    validity: list[Validity] = field(default_factory=list)


def _texts(index: DatasetIndex, notice: ElementRow) -> list[NoticeText]:
    texts = [NoticeText(text) for text in multilingual(index, child(index, notice, "Text"))]
    for container in children(index, notice, "alternativeTexts"):
        for alternative in children(index, container, "AlternativeText"):
            target = alternative.attributes.get("attributeName")
            for entry in children(index, alternative, "Text"):
                texts.extend(NoticeText(text, target) for text in multilingual(index, entry))
    return texts


def _position(index: DatasetIndex, ref: ElementRow | None, stops: list[ElementRow]) -> int | None:
    if ref is None:
        return None
    target = index.resolve(ref).target
    if target is None:
        return None
    return next((number for number, stop in enumerate(stops, 1) if stop.id == target.id), None)


def _notice_type(index: DatasetIndex, notice: ElementRow) -> Lookup:
    target, problem = follow(index, child(index, notice, "TypeOfNoticeRef"))
    if target is None:
        return problem or Lookup(LookupStatus.ABSENT)
    name = text_of(child(index, target, "Name"))
    return name if name.element else Lookup(LookupStatus.ABSENT, None, target)


def notice_view(
    index: DatasetIndex,
    assignment: ElementRow,
    scope: NoticeScope,
    stops: list[ElementRow],
    stop_position: int | None = None,
) -> NoticeView:
    """Liest eine `NoticeAssignment` und den `Notice` dahinter.

    `stop_position` (ab 1) nennt den Halt, in dem die Zuweisung eingebettet ist (Geltungsbereich
    `STOP`); sonst bestimmen `StartPointInPatternRef`/`EndPointInPatternRef` die Strecke.
    """
    ref = child(index, assignment, "NoticeRef")
    notice, problem = follow(index, ref)
    start_ref = child(index, assignment, "StartPointInPatternRef")
    end_ref = child(index, assignment, "EndPointInPatternRef")
    start = stop_position or _position(index, start_ref, stops)
    end = stop_position or _position(index, end_ref, stops)
    absent = Lookup(LookupStatus.ABSENT)
    return NoticeView(
        assignment,
        scope,
        ref,
        notice,
        problem,
        absent if notice is None else text_of(child(index, notice, "ShortCode")),
        absent if notice is None else _notice_type(index, notice),
        [] if notice is None else _texts(index, notice),
        start_ref,
        end_ref,
        start,
        end,
        validities(index, assignment),
    )


def _embedded(index: DatasetIndex, owner: ElementRow | None) -> list[ElementRow]:
    if owner is None:
        return []
    return [
        assignment
        for container in children(index, owner, "noticeAssignments")
        for assignment in children(index, container, "NoticeAssignment")
    ]


def _referencing(
    index: DatasetIndex, target: ElementRow | None, names: frozenset[str]
) -> list[ElementRow]:
    """Hinweiszuweisungen, die über eines der Ref-Elemente `names` auf das Objekt verweisen."""
    if target is None:
        return []
    found = []
    for row in index.references_to(target.id, 500):
        ref = index.element(row.element_id)
        if ref is None or ref.name not in names or ref.parent_id is None:
            continue
        parent = index.element(ref.parent_id)
        if parent is not None and parent.name == "NoticeAssignment":
            found.append(parent)
    return found


def journey_notices(
    index: DatasetIndex,
    journey: ElementRow,
    pattern: ElementRow | None,
    stops: list[ElementRow],
) -> list[NoticeView]:
    """Alle Hinweise, die zur Fahrt gehören, in Dokumentreihenfolge je Geltungsbereich."""
    seen: set[int] = set()
    views = []
    sources = (
        (NoticeScope.JOURNEY, _embedded(index, journey)),
        (NoticeScope.PATTERN, _embedded(index, pattern)),
        (
            NoticeScope.JOURNEY_REF,
            _referencing(index, journey, frozenset({"ServiceJourneyRef", "NoticedObjectRef"})),
        ),
        (
            NoticeScope.PATTERN_REF,
            _referencing(index, pattern, frozenset({"JourneyPatternRef", "NoticedObjectRef"})),
        ),
    )
    for scope, assignments in sources:
        for assignment in sorted(assignments, key=lambda item: item.id):
            if assignment.id not in seen:
                seen.add(assignment.id)
                views.append(notice_view(index, assignment, scope, stops))
    for number, stop in enumerate(stops, start=1):
        for assignment in _embedded(index, stop):
            if assignment.id not in seen:
                seen.add(assignment.id)
                views.append(notice_view(index, assignment, NoticeScope.STOP, stops, number))
    return views


def unassigned_count(index: DatasetIndex) -> int:
    """Anzahl der Hinweiszuweisungen auf Frame-Ebene ohne Verweis auf ein Objekt."""
    count = 0
    for assignment in index.elements_by_name(("NoticeAssignment",)):
        parent = None if assignment.parent_id is None else index.element(assignment.parent_id)
        container = (
            None if parent is None or parent.parent_id is None else index.element(parent.parent_id)
        )
        if container is None or not container.is_frame:
            continue
        if not any(child(index, assignment, name) for name in _OBJECT_REFS):
            count += 1
    return count
