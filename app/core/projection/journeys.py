"""Liste der Fahrten eines Datensatzes (CH 2.0): Zugnummer, Linie, Abfahrt, erster/letzter Halt.

Belege in docs/mapping.md:

- Zugnummer: `trainNumbers/TrainNumberRef` → `TrainNumber/ForAdvertisement` (F1).
- Linie: `ServiceJourneyPatternRef` → `ServiceJourneyPattern/RouteView/LineRef` → `Line` (H1, L1).
- Erster/letzter Halt: erstes/letztes `StopPointInJourneyPattern` in XML-Reihenfolge →
  `ScheduledStopPointRef` → `ScheduledStopPoint` (H2, H4). Angezeigt wird der Name des
  `ScheduledStopPoint` aus der Datei.
- Abfahrt: `DepartureTime`, `DepartureDayOffset` unverändert, falls vorhanden (Z2, M2).

Nichts wird ergänzt: Fehlt eine Angabe oder lässt sie sich nicht auflösen, steht der Grund da.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import Final

from app.core.index.dataset_index import DatasetIndex, ElementRow
from app.core.index.references import ResolveStatus, resolve

JOURNEY_TYPES: Final = ("ServiceJourney", "TemplateServiceJourney")


class LookupStatus(StrEnum):
    """Ergebnis einer Angabe in der Fahrtenliste."""

    FOUND = "found"
    ABSENT = "absent"
    """Das Element fehlt in den Daten."""
    NOT_RESOLVED = "not_resolved"
    """Die Referenz lässt sich in diesem Datensatz nicht auflösen."""
    AMBIGUOUS = "ambiguous"
    """Die Referenz passt auf mehrere Objekte."""


@dataclass(frozen=True)
class Lookup:
    """Eine Angabe mit Herkunft: Status, Text aus der Datei und Element der Quelle."""

    status: LookupStatus
    text: str | None = None
    element: ElementRow | None = None


@dataclass(frozen=True)
class JourneySummary:
    """Eine Fahrt in der Liste."""

    element: ElementRow
    train_numbers: list[Lookup]
    departure_time: Lookup
    departure_day_offset: Lookup
    line: Lookup
    first_stop: Lookup
    last_stop: Lookup


_ABSENT: Final = Lookup(LookupStatus.ABSENT)
_RESOLVE_TO_LOOKUP: Final = {
    ResolveStatus.NOT_FOUND: LookupStatus.NOT_RESOLVED,
    ResolveStatus.AMBIGUOUS: LookupStatus.AMBIGUOUS,
}


def _child(index: DatasetIndex, element: ElementRow, name: str) -> ElementRow | None:
    return next((child for child in index.children(element.id) if child.name == name), None)


def _children(index: DatasetIndex, element: ElementRow, name: str) -> list[ElementRow]:
    return [child for child in index.children(element.id) if child.name == name]


def _text(element: ElementRow | None) -> Lookup:
    if element is None or not element.text.strip():
        return _ABSENT
    return Lookup(LookupStatus.FOUND, element.text.strip(), element)


def _follow(index: DatasetIndex, ref: ElementRow | None) -> tuple[ElementRow | None, Lookup | None]:
    """Löst eine Referenz auf; liefert das Ziel oder eine Lookup-Angabe zum Grund."""
    if ref is None:
        return None, _ABSENT
    result = resolve(index, ref)
    if result.target is None:
        return None, Lookup(_RESOLVE_TO_LOOKUP[result.status], ref.attributes.get("ref"), ref)
    return result.target, None


def _train_numbers(index: DatasetIndex, journey: ElementRow) -> list[Lookup]:
    container = _child(index, journey, "trainNumbers")
    if container is None:
        return []
    numbers = []
    for ref in _children(index, container, "TrainNumberRef"):
        target, problem = _follow(index, ref)
        if target is None:
            numbers.append(problem or _ABSENT)
            continue
        advertised = _text(_child(index, target, "ForAdvertisement"))
        # Ohne ForAdvertisement bleibt die TrainNumber als Herkunft der fehlenden Angabe.
        numbers.append(
            advertised if advertised.element else Lookup(LookupStatus.ABSENT, None, target)
        )
    return numbers


def _line(index: DatasetIndex, pattern: ElementRow) -> Lookup:
    route_view = _child(index, pattern, "RouteView")
    ref = None if route_view is None else _child(index, route_view, "LineRef")
    line, problem = _follow(index, ref)
    if line is None:
        return problem or _ABSENT
    public_code = _child(index, line, "PublicCode")
    if public_code is not None and public_code.text.strip():
        return Lookup(LookupStatus.FOUND, public_code.text.strip(), public_code)
    if line.label:
        return Lookup(LookupStatus.FOUND, line.label, _child(index, line, "Name") or line)
    return Lookup(LookupStatus.ABSENT, None, line)


def _stop(index: DatasetIndex, point: ElementRow | None) -> Lookup:
    if point is None:
        return _ABSENT
    stop, problem = _follow(index, _child(index, point, "ScheduledStopPointRef"))
    if stop is None:
        return problem or _ABSENT
    if stop.label:
        return Lookup(LookupStatus.FOUND, stop.label, _child(index, stop, "Name") or stop)
    return Lookup(LookupStatus.ABSENT, None, stop)


def journey_summary(index: DatasetIndex, journey: ElementRow) -> JourneySummary:
    """Fasst eine Fahrt für die Liste zusammen."""
    pattern, pattern_problem = _follow(index, _child(index, journey, "ServiceJourneyPatternRef"))
    if pattern is None:
        line = first = last = pattern_problem or _ABSENT
    else:
        sequence = _child(index, pattern, "pointsInSequence")
        points = [] if sequence is None else _children(index, sequence, "StopPointInJourneyPattern")
        line = _line(index, pattern)
        first = _stop(index, points[0] if points else None)
        last = _stop(index, points[-1] if points else None)
    return JourneySummary(
        element=journey,
        train_numbers=_train_numbers(index, journey),
        departure_time=_text(_child(index, journey, "DepartureTime")),
        departure_day_offset=_text(_child(index, journey, "DepartureDayOffset")),
        line=line,
        first_stop=first,
        last_stop=last,
    )


def list_journeys(index: DatasetIndex) -> list[JourneySummary]:
    """Alle Fahrten (`ServiceJourney`, `TemplateServiceJourney`) in Dokumentreihenfolge."""
    return [journey_summary(index, journey) for journey in index.elements_by_name(JOURNEY_TYPES)]
