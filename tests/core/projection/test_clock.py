from __future__ import annotations

import pytest

from app.core.projection.clock import (
    ClockReading,
    parse_clock,
    parse_day_offset,
    parse_duration,
    parse_time_of_day,
    split_seconds,
)


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("00:00:00", 0),
        ("10:35:00", 38100),
        (" 23:59:59 ", 86399),
        ("24:00:00", None),
        ("10:60:00", None),
        ("10:35", None),
        ("10:35:00Z", None),
        ("10:35:00+01:00", None),
        ("10:35:00.5", None),
        ("", None),
    ],
)
def test_parse_time_of_day(text: str, expected: int | None) -> None:
    assert parse_time_of_day(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("10:35:00", ClockReading(38100, False)),
        (" 02:33:00Z ", ClockReading(2 * 3600 + 33 * 60, True)),
        ("23:59:59Z", ClockReading(86399, True)),
        ("24:00:00Z", None),
        ("10:35:00z", None),
        ("10:35:00+01:00", None),
        ("10:35:00-05:00", None),
        ("10:35Z", None),
        ("", None),
    ],
)
def test_parse_clock_marks_utc_and_rejects_other_zones(
    text: str, expected: ClockReading | None
) -> None:
    assert parse_clock(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("PT10M", 600),
        ("PT1H5M", 3900),
        ("PT10M10S", 610),
        ("PT0S", 0),
        ("P1D", 86400),
        ("P1DT2H", 93600),
        ("PT6H32M", 23520),
        ("P3M", None),
        ("P1Y", None),
        ("P", None),
        ("PT", None),
        ("P1DT", None),
        ("PT1.5S", None),
        ("-PT5M", None),
        ("10", None),
        ("", None),
    ],
)
def test_parse_duration(text: str, expected: int | None) -> None:
    assert parse_duration(text) == expected


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("0", 0),
        ("1", 1),
        (" -1 ", -1),
        ("+2", 2),
        ("366", 366),
        ("367", None),
        ("a", None),
        ("", None),
    ],
)
def test_parse_day_offset(text: str, expected: int | None) -> None:
    assert parse_day_offset(text) == expected


@pytest.mark.parametrize(
    ("total", "expected"),
    [
        (0, (0, "00:00:00")),
        (38100, (0, "10:35:00")),
        (86400, (1, "00:00:00")),
        (86400 + 38100, (1, "10:35:00")),
        (-3600, (-1, "23:00:00")),
        (2 * 86400 + 59, (2, "00:00:59")),
    ],
)
def test_split_seconds(total: int, expected: tuple[int, str]) -> None:
    assert split_seconds(total) == expected
