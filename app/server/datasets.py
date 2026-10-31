"""Geöffnete Datensätze des Servers mit nicht erratbaren IDs.

Die Schnittstelle nimmt nie Dateipfade entgegen, nur diese IDs. Objekt-IDs haben die Form
`<Datensatz-ID>.<Elementnummer>`.
"""

from __future__ import annotations

import re
import secrets
import threading
from collections import OrderedDict
from typing import Final

from app.core.dataset import Dataset

MAX_OPEN_DATASETS: Final = 10
_TOKEN_BYTES: Final = 16
_DATASET_ID = re.compile(r"^[A-Za-z0-9_-]{16,64}$")
_OBJECT_ID = re.compile(r"^([A-Za-z0-9_-]{16,64})\.([1-9][0-9]{0,9})$")


class DatasetRegistry:
    """Hält die zuletzt geöffneten Datensätze; der älteste fällt bei Überlauf heraus.

    Herausfallen und Schliessen nehmen den Datensatz aus der Liste und rufen `Dataset.close` auf.
    Läuft noch eine Anfrage mit dem Datensatz, wirkt das Schliessen erst nach deren Ende; die
    Anfrage wird nicht abgebrochen.
    """

    def __init__(self, max_open: int = MAX_OPEN_DATASETS) -> None:
        self._lock = threading.Lock()
        self._max_open = max_open
        self._datasets: OrderedDict[str, Dataset] = OrderedDict()

    def add(self, dataset: Dataset) -> str:
        """Nimmt einen Datensatz auf und gibt seine ID zurück."""
        dataset_id = secrets.token_urlsafe(_TOKEN_BYTES)
        with self._lock:
            self._datasets[dataset_id] = dataset
            evicted = []
            while len(self._datasets) > self._max_open:
                evicted.append(self._datasets.popitem(last=False)[1])
        for old in evicted:
            old.close()
        return dataset_id

    def remove(self, dataset_id: str) -> bool:
        """Schliesst einen Datensatz (nach laufenden Anfragen); `False`, wenn unbekannt."""
        if not _DATASET_ID.match(dataset_id):
            return False
        with self._lock:
            dataset = self._datasets.pop(dataset_id, None)
        if dataset is None:
            return False
        dataset.close()
        return True

    def get(self, dataset_id: str) -> Dataset | None:
        """Datensatz zur ID; `None` bei unbekannter oder ungültiger ID."""
        if not _DATASET_ID.match(dataset_id):
            return None
        with self._lock:
            dataset = self._datasets.get(dataset_id)
            if dataset is not None:
                self._datasets.move_to_end(dataset_id)
            return dataset

    def acquire(self, dataset_id: str) -> Dataset | None:
        """Datensatz zur ID, für die Dauer einer Anfrage festgehalten (`Dataset.release` folgt).

        `None` bei unbekannter ID oder wenn der Datensatz gerade geschlossen wird.
        """
        dataset = self.get(dataset_id)
        if dataset is None or not dataset.acquire():
            return None
        return dataset

    def close_all(self) -> None:
        """Schliesst alle Datensätze."""
        with self._lock:
            for dataset in self._datasets.values():
                dataset.close()
            self._datasets.clear()


def object_id(dataset_id: str, element_id: int) -> str:
    """Objekt-ID für die Schnittstelle."""
    return f"{dataset_id}.{element_id}"


def parse_object_id(value: str) -> tuple[str, int] | None:
    """Zerlegt eine Objekt-ID; `None`, wenn sie nicht das erwartete Format hat."""
    match = _OBJECT_ID.match(value)
    return None if match is None else (match.group(1), int(match.group(2)))
