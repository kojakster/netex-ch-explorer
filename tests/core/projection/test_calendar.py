from __future__ import annotations

import datetime as dt

import pytest

from app.core.dataset import SourceFile, open_dataset
from app.core.index.dataset_index import DatasetIndex, ElementRow
from app.core.messages import MessageKey
from app.core.projection.calendar import (
    MAX_LISTED_DAYS,
    OperatingDays,
    dst_changes,
    dst_nights,
    operating_days,
    validities,
)
from app.core.projection.common import LookupStatus
from tests.support import REF_TARGETS


def condition(
    from_date: str | None, to_date: str | None, bits: str | None
) -> tuple[DatasetIndex, ElementRow]:
    parts = []
    if from_date is not None:
        parts.append(f"<FromDate>{from_date}</FromDate>")
    if to_date is not None:
        parts.append(f"<ToDate>{to_date}</ToDate>")
    if bits is not None:
        parts.append(f"<ValidDayBits>{bits}</ValidDayBits>")
    xml = f"<R><AvailabilityCondition id='c'>{''.join(parts)}</AvailabilityCondition></R>"
    index = open_dataset([SourceFile("t", xml.encode())], (), REF_TARGETS).index
    return index, index.elements_by_name(["AvailabilityCondition"])[0]


def days_of(from_date: str | None, to_date: str | None, bits: str | None) -> OperatingDays:
    index, element = condition(from_date, to_date, bits)
    return operating_days(index, element)


def keys(days: OperatingDays) -> list[MessageKey]:
    return [finding.key for finding in days.findings]


def test_days_from_bits() -> None:
    days = days_of("2026-12-13T00:00:00", "2026-12-19T23:59:59", "0111110")
    assert days.period_days == 7
    assert days.valid_count == 5
    assert days.days_listed
    assert [day.isoformat() for day in days.days] == [
        "2026-12-14",
        "2026-12-15",
        "2026-12-16",
        "2026-12-17",
        "2026-12-18",
    ]
    assert days.findings == ()
    assert days.from_date is not None
    assert days.valid_day_bits is not None


def test_single_day_pattern() -> None:
    days = days_of("2026-03-14T00:00:00", "2026-03-14T23:59:59", "1")
    assert [day.isoformat() for day in days.days] == ["2026-03-14"]


def test_bits_length_mismatch_does_not_guess_days() -> None:
    days = days_of("2026-12-13", "2026-12-19", "0111110111")
    assert not days.days_listed
    assert days.days == ()
    assert days.valid_count == 8
    assert keys(days) == [MessageKey.AVAILABILITY_BITS_LENGTH]
    assert days.findings[0].params == {"bits": 10, "days": 7}


def test_too_long_period_is_not_listed() -> None:
    length = MAX_LISTED_DAYS + 1
    to_date = (dt.date(2026, 1, 1) + dt.timedelta(days=length - 1)).isoformat()
    days = days_of("2026-01-01", to_date, "1" * length)
    assert not days.days_listed
    assert days.valid_count == length


@pytest.mark.parametrize(
    ("from_date", "to_date", "bits", "expected"),
    [
        (None, "2026-12-19", "1", [MessageKey.AVAILABILITY_ELEMENT_MISSING]),
        ("2026-12-13", None, "1", [MessageKey.AVAILABILITY_ELEMENT_MISSING]),
        ("2026-12-13", "2026-12-13", None, [MessageKey.AVAILABILITY_ELEMENT_MISSING]),
        ("kein Datum", "2026-12-13", "1", [MessageKey.AVAILABILITY_DATE_INVALID]),
        ("2026-12-14", "2026-12-13", "1", [MessageKey.AVAILABILITY_RANGE_INVALID]),
        ("2026-12-13", "2026-12-13", "12", [MessageKey.AVAILABILITY_BITS_INVALID]),
    ],
)
def test_problems_are_reported(
    from_date: str | None, to_date: str | None, bits: str | None, expected: list[MessageKey]
) -> None:
    days = days_of(from_date, to_date, bits)
    assert keys(days) == expected
    assert days.days == ()


def test_validities_follow_references() -> None:
    xml = (
        "<R><ServiceJourney id='j'><validityConditions>"
        "<AvailabilityConditionRef ref='c'/><AvailabilityConditionRef ref='fehlt'/>"
        "</validityConditions></ServiceJourney>"
        "<AvailabilityCondition id='c'><FromDate>2026-01-01</FromDate>"
        "<ToDate>2026-01-02</ToDate><ValidDayBits>10</ValidDayBits></AvailabilityCondition></R>"
    )
    index = open_dataset([SourceFile("t", xml.encode())], (), REF_TARGETS).index
    journey = index.elements_by_name(["ServiceJourney"])[0]
    first, second = validities(index, journey)
    assert first.days is not None
    assert [day.isoformat() for day in first.days.days] == ["2026-01-01"]
    assert second.days is None
    assert second.problem is not None
    assert second.problem.status is LookupStatus.NOT_RESOLVED


def test_dst_changes_are_last_sundays() -> None:
    assert dst_changes(2026) == (dt.date(2026, 3, 29), dt.date(2026, 10, 25))
    assert dst_changes(2027) == (dt.date(2027, 3, 28), dt.date(2027, 10, 31))
    assert dst_changes(2025) == (dt.date(2025, 3, 30), dt.date(2025, 10, 26))


HOUR = 3600


def test_dst_night_touched_by_overnight_journey() -> None:
    saturday = (dt.date(2026, 3, 28),)
    nights = dst_nights(saturday, 23 * HOUR, 24 * HOUR + 4 * HOUR)
    assert [(night.date, night.forward) for night in nights] == [(dt.date(2026, 3, 29), True)]


def test_dst_night_autumn_is_marked_as_back() -> None:
    nights = dst_nights((dt.date(2026, 10, 24),), 23 * HOUR, 27 * HOUR)
    assert [(night.date, night.forward) for night in nights] == [(dt.date(2026, 10, 25), False)]


def test_dst_night_journey_with_day_offset() -> None:
    # Betriebstag 28.3., Abfahrt 01:30 am 29.3. (DepartureDayOffset 1), Ende 02:30.
    nights = dst_nights((dt.date(2026, 3, 28),), 24 * HOUR + 90 * 60, 24 * HOUR + 150 * 60)
    assert [night.date for night in nights] == [dt.date(2026, 3, 29)]


def test_no_dst_night_before_or_after_the_hour() -> None:
    assert dst_nights((dt.date(2026, 3, 29),), 3 * HOUR, 5 * HOUR) == []
    assert dst_nights((dt.date(2026, 3, 29),), 0, 2 * HOUR) == []
    assert dst_nights((dt.date(2026, 3, 29),), 8 * HOUR, 9 * HOUR) == []
    assert dst_nights((dt.date(2026, 6, 1),), 0, 30 * HOUR) == []


def test_dst_nights_are_unique_and_sorted() -> None:
    days = (dt.date(2026, 3, 28), dt.date(2026, 3, 29), dt.date(2026, 10, 24))
    nights = dst_nights(days, 23 * HOUR, 27 * HOUR)
    assert [night.date for night in nights] == [dt.date(2026, 3, 29), dt.date(2026, 10, 25)]
