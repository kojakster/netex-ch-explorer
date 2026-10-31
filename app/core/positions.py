"""Positionen in einer Datei: Byte-Offset, Zeichen-Offset, Zeile und Spalte.

Der Byte-Offset zählt ab Dateianfang (inklusive BOM). Zeichen-Offset, Zeile und Spalte beziehen
sich auf den angezeigten Text ohne BOM; Zeile und Spalte beginnen bei 1, die Spalte zählt
Zeichen (nicht Bytes).
"""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Position:
    """Eine Stelle in einer Datei."""

    byte: int
    char: int
    line: int
    column: int


class PositionTracker:
    """Rechnet Byte-Offsets in Positionen um; schnell bei aufsteigenden Offsets.

    Die Daten müssen UTF-8 sein (`text_start` = Länge des BOM oder 0).
    """

    def __init__(self, data: bytes, text_start: int) -> None:
        self._data = data
        self._text_start = text_start
        self._reset()

    def _reset(self) -> None:
        self._byte = self._text_start
        self._char = 0
        self._line = 1
        self._line_start_char = 0

    def position(self, byte: int) -> Position:
        """Gibt die Position zum Byte-Offset zurück (Offsets vor dem BOM gelten als Textanfang)."""
        byte = max(byte, self._text_start)
        if byte < self._byte:
            self._reset()
        segment = self._data[self._byte : byte].decode("utf-8", errors="replace")
        newline = segment.rfind("\n")
        if newline >= 0:
            self._line += segment.count("\n")
            self._line_start_char = self._char + newline + 1
        self._char += len(segment)
        self._byte = byte
        return Position(
            byte=byte,
            char=self._char,
            line=self._line,
            column=self._char - self._line_start_char + 1,
        )
