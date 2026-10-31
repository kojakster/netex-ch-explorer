"""Betriebstage (`AvailabilityCondition`) und Nächte der Zeitumstellung.

Belege in docs/mapping.md: B1 bis B5 (Betriebstage), Z8 (Zeitumstellung).

- Betriebstage kommen aus `AvailabilityCondition` (`FromDate`, `ToDate`, `ValidDayBits`): ein Bit
  je Kalendertag des Zeitraums, `1` = gültig. Es gibt keine Pauschalaussagen wie „Mo bis Fr“.
- Stimmt die Länge der Bits nicht mit dem Zeitraum überein, werden die Tage **nicht** aufgelistet
  (die Zuordnung der Bits zu Tagen wäre geraten); die Anzahl gesetzter Bits bleibt sichtbar.
"""

from __future__ import annotations

import datetime as dt
import re
from dataclasses import dataclass
from typing import Final

from app.core.index.dataset_index import DatasetIndex, ElementRow
from app.core.messages import MessageKey, Severity
from app.core.projection.clock import SECONDS_PER_DAY, SECONDS_PER_HOUR
from app.core.projection.common import Finding, Lookup, child, children, follow, text_of

MAX_LISTED_DAYS: Final = 3660
"""Höchstens so viele Tage werden aufgelistet (rund zehn Jahre)."""
_DATE_LENGTH: Final = 10
_BITS = re.compile(r"[01]+")
_SUNDAY: Final = 6
_MARCH: Final = 3
_OCTOBER: Final = 10
_DECEMBER: Final = 12
_TRANSITION_START_HOUR: Final = 2
_TRANSITION_END_HOUR: Final = 3
_MAX_DST_NIGHTS: Final = 20


@dataclass(frozen=True)
class OperatingDays:
    """Betriebstage einer `AvailabilityCondition` mit Herkunft jeder Angabe."""

    condition: ElementRow
    from_date: ElementRow | None
    to_date: ElementRow | None
    valid_day_bits: ElementRow | None
    first_day: dt.date | None
    last_day: dt.date | None
    period_days: int | None
    valid_count: int | None
    """Anzahl der Bits `1`; `None`, wenn `ValidDayBits` fehlt oder ungültig ist."""
    days: tuple[dt.date, ...]
    """Die gültigen Tage; leer, wenn sie sich nicht sicher bestimmen lassen."""
    days_listed: bool
    findings: tuple[Finding, ...]


def _parse_date(text: str) -> dt.date | None:
    try:
        return dt.date.fromisoformat(text.strip()[:_DATE_LENGTH])
    except ValueError:
        return None


def _date_of(
    index: DatasetIndex, condition: ElementRow, name: str, findings: list[Finding]
) -> tuple[ElementRow | None, dt.date | None]:
    element = child(index, condition, name)
    value = text_of(element)
    if element is None or value.text is None:
        findings.append(
            Finding(
                Severity.WARNING,
                MessageKey.AVAILABILITY_ELEMENT_MISSING,
                {"element": name},
                condition,
            )
        )
        return element, None
    parsed = _parse_date(value.text)
    if parsed is None:
        findings.append(
            Finding(
                Severity.WARNING,
                MessageKey.AVAILABILITY_DATE_INVALID,
                {"element": name, "value": value.text},
                element,
            )
        )
    return element, parsed


def _bits_of(
    index: DatasetIndex, condition: ElementRow, findings: list[Finding]
) -> tuple[ElementRow | None, str | None]:
    element = child(index, condition, "ValidDayBits")
    value = text_of(element)
    if element is None or value.text is None:
        findings.append(
            Finding(
                Severity.WARNING,
                MessageKey.AVAILABILITY_ELEMENT_MISSING,
                {"element": "ValidDayBits"},
                condition,
            )
        )
        return element, None
    if _BITS.fullmatch(value.text) is None:
        findings.append(
            Finding(Severity.WARNING, MessageKey.AVAILABILITY_BITS_INVALID, {}, element)
        )
        return element, None
    return element, value.text


def operating_days(index: DatasetIndex, condition: ElementRow) -> OperatingDays:
    """Liest eine `AvailabilityCondition`; Probleme stehen in `findings`, nichts wird ergänzt."""
    findings: list[Finding] = []
    from_element, first = _date_of(index, condition, "FromDate", findings)
    to_element, last = _date_of(index, condition, "ToDate", findings)
    bits_element, bits = _bits_of(index, condition, findings)
    period = None
    if first is not None and last is not None:
        if last < first:
            findings.append(
                Finding(Severity.WARNING, MessageKey.AVAILABILITY_RANGE_INVALID, {}, condition)
            )
        else:
            period = (last - first).days + 1
    days: tuple[dt.date, ...] = ()
    listed = False
    if bits is not None and first is not None and period is not None:
        if len(bits) != period:
            findings.append(
                Finding(
                    Severity.WARNING,
                    MessageKey.AVAILABILITY_BITS_LENGTH,
                    {"bits": len(bits), "days": period},
                    bits_element,
                )
            )
        elif period <= MAX_LISTED_DAYS:
            days = tuple(
                first + dt.timedelta(days=position)
                for position, bit in enumerate(bits)
                if bit == "1"
            )
            listed = True
    return OperatingDays(
        condition=condition,
        from_date=from_element,
        to_date=to_element,
        valid_day_bits=bits_element,
        first_day=first,
        last_day=last,
        period_days=period,
        valid_count=None if bits is None else bits.count("1"),
        days=days,
        days_listed=listed,
        findings=tuple(findings),
    )


@dataclass(frozen=True)
class Validity:
    """Eine `AvailabilityConditionRef` mit den Betriebstagen oder dem Grund, warum nicht."""

    ref: ElementRow
    days: OperatingDays | None
    problem: Lookup | None


def validities(index: DatasetIndex, owner: ElementRow) -> list[Validity]:
    """Alle `AvailabilityConditionRef` unter `validityConditions` eines Elements (B1)."""
    result = []
    for container in children(index, owner, "validityConditions"):
        for ref in children(index, container, "AvailabilityConditionRef"):
            condition, problem = follow(index, ref)
            result.append(
                Validity(
                    ref, None if condition is None else operating_days(index, condition), problem
                )
            )
    return result


@dataclass(frozen=True)
class DstNight:
    """Eine Nacht der Zeitumstellung, die eine Fahrt berührt."""

    date: dt.date
    forward: bool
    """`True` im März (02:00 → 03:00), `False` im Oktober (03:00 → 02:00)."""


def _first_of_next_month(year: int, month: int) -> dt.date:
    return dt.date(year + 1, 1, 1) if month == _DECEMBER else dt.date(year, month + 1, 1)


def _last_sunday(year: int, month: int) -> dt.date:
    day = _first_of_next_month(year, month) - dt.timedelta(days=1)
    return day - dt.timedelta(days=(day.weekday() - _SUNDAY) % 7)


def dst_changes(year: int) -> tuple[dt.date, dt.date]:
    """Tage der Zeitumstellung in der Schweiz: letzter Sonntag im März und im Oktober."""
    return _last_sunday(year, _MARCH), _last_sunday(year, _OCTOBER)


def dst_nights(days: tuple[dt.date, ...], start: int, end: int) -> list[DstNight]:
    """Nächte der Zeitumstellung, in denen eine Fahrt zwischen `start` und `end` unterwegs ist.

    `start`/`end` sind Sekunden seit Mitternacht des Betriebstags (auch über 24 Stunden). Berührt
    ist eine Nacht, wenn die Fahrt die Ortszeit zwischen 02:00 und 03:00 des Umstellungstags
    überlappt; dann ist die Dauer bei Ortszeit ohne Zone nicht eindeutig.
    """
    changes: dict[dt.date, bool] = {}
    for year in {day.year for day in days} | {day.year + 1 for day in days}:
        march, october = dst_changes(year)
        changes[march] = True
        changes[october] = False
    found: dict[dt.date, bool] = {}
    first_offset, last_offset = start // SECONDS_PER_DAY, end // SECONDS_PER_DAY
    for day in days:
        for offset in range(first_offset, last_offset + 1):
            candidate = day + dt.timedelta(days=offset)
            if candidate not in changes:
                continue
            begin = offset * SECONDS_PER_DAY + _TRANSITION_START_HOUR * SECONDS_PER_HOUR
            finish = offset * SECONDS_PER_DAY + _TRANSITION_END_HOUR * SECONDS_PER_HOUR
            if start < finish and end > begin:
                found[candidate] = changes[candidate]
    return [DstNight(night, found[night]) for night in sorted(found)][:_MAX_DST_NIGHTS]
