"""Farbschlüssel einer Angabe: Frame-Typ, unbekannter Frame oder Grau."""

from __future__ import annotations

from typing import Final

from app.core.config import DEFAULT_FRAME_COLORS
from app.core.index.dataset_index import ElementRow

KNOWN_FRAMES: Final = tuple(key for key in DEFAULT_FRAME_COLORS if key.endswith("Frame"))
UNKNOWN_FRAME: Final = "unknown"
NOT_RELEVANT: Final = "notRelevant"


def color_key(element: ElementRow, frame: ElementRow | None) -> str | None:
    """Schlüssel in `frame-colors.json`; `None`, wenn das Element in keinem Frame steht."""
    if element.not_relevant:
        return NOT_RELEVANT
    if frame is None:
        return None
    return frame.name if frame.name in KNOWN_FRAMES else UNKNOWN_FRAME
