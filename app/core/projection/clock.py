"""Zeitangaben lesen: `hh:mm:ss`, ISO-8601-Dauer und ganze Tage, ohne Ersatzwerte.

Zeiten sind Ortszeit ohne Zeitzone (docs/mapping.md, Z6). Einzige Ausnahme ist der Sonderfall der
Zeitumstellung: `hh:mm:ssZ` ist UTC (Z9). UTC wird nur als Kennzeichen gelesen und nie in Ortszeit
umgerechnet. Alles, was nicht eindeutig lesbar ist (andere Zeitzonen, Monate, Jahre, Bruchteile),
ergibt `None`; die Fahrtansicht meldet dann „nicht berechenbar“, statt etwas zu raten.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Final

SECONDS_PER_MINUTE: Final = 60
SECONDS_PER_HOUR: Final = 3600
SECONDS_PER_DAY: Final = 86400
MAX_DAY_OFFSET: Final = 366
"""Grösster Betrag einer Tagesverschiebung, den die Fahrtansicht als sinnvoll annimmt."""

_TIME = re.compile(r"(\d{2}):(\d{2}):(\d{2})(Z?)")
_DURATION = re.compile(r"P(?:(\d+)D)?(?:T(?:(\d+)H)?(?:(\d+)M)?(?:(\d+)S)?)?")
_INTEGER = re.compile(r"[+-]?\d+")
_MAX_HOUR: Final = 23
_MAX_MINUTE_OR_SECOND: Final = 59


@dataclass(frozen=True)
class ClockReading:
    """Eine gelesene Uhrzeit: Sekunden seit Mitternacht und ob sie UTC (`Z`) ist."""

    seconds: int
    utc: bool


def parse_clock(text: str) -> ClockReading | None:
    """Liest `hh:mm:ss` (Ortszeit) oder `hh:mm:ssZ` (UTC); sonst `None`.

    Andere Zeitzonen (`+01:00` usw.) werden nicht gelesen. Es findet keine Umrechnung statt.
    """
    match = _TIME.fullmatch(text.strip())
    if match is None:
        return None
    hours, minutes, seconds = (int(part) for part in match.groups()[:3])
    if hours > _MAX_HOUR or minutes > _MAX_MINUTE_OR_SECOND or seconds > _MAX_MINUTE_OR_SECOND:
        return None
    total = hours * SECONDS_PER_HOUR + minutes * SECONDS_PER_MINUTE + seconds
    return ClockReading(total, match.group(4) == "Z")


def parse_time_of_day(text: str) -> int | None:
    """Sekunden seit Mitternacht für Ortszeit `hh:mm:ss`; `None`, wenn das Format nicht passt.

    Eine UTC-Zeit (`hh:mm:ssZ`) ergibt hier `None`: Wer sie lesen will, nutzt `parse_clock`.
    """
    reading = parse_clock(text)
    return None if reading is None or reading.utc else reading.seconds


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
