"""Zeitangaben lesen: `hh:mm:ss`, ISO-8601-Dauer und ganze Tage, ohne Ersatzwerte.

Zeiten sind Ortszeit ohne Zeitzone (docs/mapping.md, Z6). Alles, was nicht eindeutig lesbar ist
(Zeitzone, Monate, Jahre, Bruchteile), ergibt `None`; die Fahrtansicht meldet dann „nicht
berechenbar“, statt etwas zu raten.
"""

from __future__ import annotations

import re
from typing import Final

SECONDS_PER_MINUTE: Final = 60
SECONDS_PER_HOUR: Final = 3600
SECONDS_PER_DAY: Final = 86400
MAX_DAY_OFFSET: Final = 366
"""Grösster Betrag einer Tagesverschiebung, den die Fahrtansicht als sinnvoll annimmt."""

_TIME = re.compile(r"(\d{2}):(\d{2}):(\d{2})")
_DURATION = re.compile(r"P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?")
_INTEGER = re.compile(r"[+-]?\d+")
_MAX_HOUR: Final = 23
_MAX_MINUTE_OR_SECOND: Final = 59


def parse_time_of_day(text: str) -> int | None:
    """Sekunden seit Mitternacht für `hh:mm:ss`; `None`, wenn das Format nicht passt."""
    match = _TIME.fullmatch(text.strip())
    if match is None:
        return None
    hours, minutes, seconds = (int(part) for part in match.groups())
    if hours > _MAX_HOUR or minutes > _MAX_MINUTE_OR_SECOND or seconds > _MAX_MINUTE_OR_SECOND:
        return None
    return hours * SECONDS_PER_HOUR + minutes * SECONDS_PER_MINUTE + seconds


def parse_duration(text: str) -> int | None:
    """Sekunden einer Dauer (`PT10M`, `PT1H5M`, `PT10M10S`, `P1DT2H`); sonst `None`.

    Monate und Jahre sind keine feste Dauer und werden nicht gelesen. Eine leere Dauer (`P`, `PT`)
    ist ungültig.
    """
    stripped = text.strip()
    match = _DURATION.fullmatch(stripped)
    if match is None or stripped in {"P", "PT"} or stripped.endswith("T"):
        return None
    days, hours, minutes, seconds = (int(part) if part else 0 for part in match.groups())
    return (
        days * SECONDS_PER_DAY + hours * SECONDS_PER_HOUR + minutes * SECONDS_PER_MINUTE + seconds
    )


def parse_day_offset(text: str) -> int | None:
    """Ganze Tagesverschiebung (auch negativ); `None` bei anderem Format oder unsinnigem Wert."""
    stripped = text.strip()
    if _INTEGER.fullmatch(stripped) is None:
        return None
    value = int(stripped)
    return value if abs(value) <= MAX_DAY_OFFSET else None


def split_seconds(total: int) -> tuple[int, str]:
    """Zerlegt Sekunden seit Mitternacht des Betriebstags in (Tagesverschiebung, `hh:mm:ss`)."""
    day, rest = divmod(total, SECONDS_PER_DAY)
    hours, remainder = divmod(rest, SECONDS_PER_HOUR)
    minutes, seconds = divmod(remainder, SECONDS_PER_MINUTE)
    return day, f"{hours:02d}:{minutes:02d}:{seconds:02d}"
