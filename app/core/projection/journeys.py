"""Liste der Fahrten eines Datensatzes (CH 2.0): Zugnummer, Linie, Abfahrt, erster/letzter Halt.

Belege in docs/mapping.md:

- Zugnummer: `trainNumbers/TrainNumberRef` → `TrainNumber/ForAdvertisement` (F1).
- Linie: `ServiceJourneyPatternRef` → `ServiceJourneyPattern/RouteView/LineRef` → `Line` (H1, L1).
- Erster/letzter Halt: erstes/letztes `StopPointInJourneyPattern` in XML-Reihenfolge →
  `ScheduledStopPointRef` → `ScheduledStopPoint` (H2, H4). Angezeigt wird der Name des
  `ScheduledStopPoint` aus der Datei.
- Produktkategorie: `TypeOfProductCategoryRef` → `TypeOfProductCategory/ShortName` der Fahrt.
- Abfahrt: `DepartureTime`, `DepartureDayOffset` unverändert, falls vorhanden (Z2, M2).

Nichts wird ergänzt: Fehlt eine Angabe oder lässt sie sich nicht auflösen, steht der Grund da.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from app.core.index.dataset_index import DatasetIndex, ElementRow
from app.core.projection.common import (
    ABSENT,
    Lookup,
    LookupStatus,
    child,
    children,
    follow,
    text_of,
)

JOURNEY_TYPES: Final = ("ServiceJourney", "TemplateServiceJourney")


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
    category: Lookup
    """`ShortName` der `TypeOfProductCategory` der Fahrt (Abzeichen in der Liste)."""


def train_number(index: DatasetIndex, ref: ElementRow) -> Lookup:
    """Zugnummer (`ForAdvertisement`) hinter einer `TrainNumberRef`."""
    target, problem = follow(index, ref)
    if target is None:
        return problem or ABSENT
    advertised = text_of(child(index, target, "ForAdvertisement"))
    # Ohne ForAdvertisement bleibt die TrainNumber als Herkunft der fehlenden Angabe.
    return advertised if advertised.element else Lookup(LookupStatus.ABSENT, None, target)


def train_numbers_of(index: DatasetIndex, journey: ElementRow) -> list[Lookup]:
    """Zugnummern der Fahrt (`trainNumbers/TrainNumberRef`), je Verweis eine Angabe mit Herkunft."""
    container = child(index, journey, "trainNumbers")
    if container is None:
        return []
    return [train_number(index, ref) for ref in children(index, container, "TrainNumberRef")]


def line_of(index: DatasetIndex, pattern: ElementRow) -> Lookup:
    """Linie des Fahrtmusters: `PublicCode`, sonst `Name` der `Line`."""
    route_view = child(index, pattern, "RouteView")
    ref = None if route_view is None else child(index, route_view, "LineRef")
    line, problem = follow(index, ref)
    if line is None:
        return problem or ABSENT
    public_code = child(index, line, "PublicCode")
    if public_code is not None and public_code.text.strip():
        return Lookup(LookupStatus.FOUND, public_code.text.strip(), public_code)
    if line.label:
        return Lookup(LookupStatus.FOUND, line.label, child(index, line, "Name") or line)
    return Lookup(LookupStatus.ABSENT, None, line)


def stop_name(index: DatasetIndex, point: ElementRow | None) -> Lookup:
    """Name des `ScheduledStopPoint` eines `StopPointInJourneyPattern`."""
    if point is None:
        return ABSENT
    stop, problem = follow(index, child(index, point, "ScheduledStopPointRef"))
    if stop is None:
        return problem or ABSENT
    if stop.label:
        return Lookup(LookupStatus.FOUND, stop.label, child(index, stop, "Name") or stop)
    return Lookup(LookupStatus.ABSENT, None, stop)


def category_short_name(index: DatasetIndex, journey: ElementRow) -> Lookup:
    """`ShortName` der `TypeOfProductCategory`, auf die die Fahrt verweist (sonst der Grund)."""
    ref = child(index, journey, "TypeOfProductCategoryRef")
    if ref is None:
        return ABSENT
    target, problem = follow(index, ref)
    if target is None:
        return problem or ABSENT
    return text_of(child(index, target, "ShortName"))


def journey_summary(index: DatasetIndex, journey: ElementRow) -> JourneySummary:
    """Fasst eine Fahrt für die Liste zusammen."""
    pattern, pattern_problem = follow(index, child(index, journey, "ServiceJourneyPatternRef"))
    if pattern is None:
        line = first = last = pattern_problem or ABSENT
    else:
        sequence = child(index, pattern, "pointsInSequence")
        points = [] if sequence is None else children(index, sequence, "StopPointInJourneyPattern")
        line = line_of(index, pattern)
        first = stop_name(index, points[0] if points else None)
        last = stop_name(index, points[-1] if points else None)
    return JourneySummary(
        element=journey,
        train_numbers=train_numbers_of(index, journey),
        departure_time=text_of(child(index, journey, "DepartureTime")),
        departure_day_offset=text_of(child(index, journey, "DepartureDayOffset")),
        line=line,
        first_stop=first,
        last_stop=last,
        category=category_short_name(index, journey),
    )


def list_journeys(index: DatasetIndex) -> list[JourneySummary]:
    """Alle Fahrten (`ServiceJourney`, `TemplateServiceJourney`) in Dokumentreihenfolge."""
    return [journey_summary(index, journey) for journey in index.elements_by_name(JOURNEY_TYPES)]
