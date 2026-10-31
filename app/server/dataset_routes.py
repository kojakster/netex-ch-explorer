"""Endpunkte für Datensätze, Objekte, Fahrten, Diagnosen und XML-Ausschnitte (docs/api.md)."""

from __future__ import annotations

from typing import Annotated, Final

from fastapi import APIRouter, HTTPException, Query
from starlette.status import HTTP_404_NOT_FOUND

from app.core.dataset import Dataset, SourceFile, open_dataset
from app.core.diagnostics import DiagnosticCategory
from app.core.explorer import element_xml_window, object_detail, position_xml_window
from app.core.guide.examples import Example, read_example
from app.core.messages import Severity
from app.core.projection.journeys import list_journeys
from app.server.dataset_schemas import (
    Converter,
    DatasetOut,
    DiagnosticOut,
    JourneyOut,
    ObjectDetailOut,
    ObjectSearchOut,
    OpenDatasetIn,
    XmlWindowOut,
)
from app.server.datasets import DatasetRegistry, parse_object_id
from app.server.runtime import Runtime

MAX_SEARCH_LIMIT: Final = 200
DEFAULT_SEARCH_LIMIT: Final = 50
MAX_QUERY_LENGTH: Final = 200


def _not_found() -> HTTPException:
    return HTTPException(status_code=HTTP_404_NOT_FOUND)


class _Lookup:
    """Sucht Datensätze und Elemente; unbekannte oder ungültige IDs ergeben 404."""

    def __init__(self, registry: DatasetRegistry) -> None:
        self.registry = registry

    def dataset(self, dataset_id: str) -> Dataset:
        dataset = self.registry.get(dataset_id)
        if dataset is None:
            raise _not_found()
        return dataset

    def element(self, value: str) -> tuple[str, Dataset, int]:
        parsed = parse_object_id(value)
        if parsed is None:
            raise _not_found()
        dataset_id, element_id = parsed
        return dataset_id, self.dataset(dataset_id), element_id


def dataset_router(runtime: Runtime, registry: DatasetRegistry) -> APIRouter:
    """Router für Datensätze: öffnen, Übersicht, Fahrten, Objektsuche, Diagnosen, XML an Stelle."""
    router = APIRouter(prefix="/api")
    examples = [Example(status.name, status.title) for status in runtime.guide.examples]
    not_relevant = runtime.config.not_relevant_elements
    lookup = _Lookup(registry)

    @router.post("/datasets")
    def open_example(request: OpenDatasetIn) -> DatasetOut:
        """Öffnet ein Beispiel des Guides (nur Namen aus der Beispielliste, nie Pfade)."""
        data = read_example(runtime.config.settings.guide_path, request.example, examples)
        if data is None:
            raise _not_found()
        dataset = open_dataset([SourceFile(request.example, data)], not_relevant)
        dataset_id = registry.add(dataset)
        return Converter(dataset_id, dataset).dataset()

    @router.get("/datasets/{dataset_id}")
    def get_dataset(dataset_id: str) -> DatasetOut:
        """Übersicht über einen geöffneten Datensatz."""
        return Converter(dataset_id, lookup.dataset(dataset_id)).dataset()

    @router.get("/datasets/{dataset_id}/journeys")
    def get_journeys(dataset_id: str) -> list[JourneyOut]:
        """Liste der Fahrten."""
        dataset = lookup.dataset(dataset_id)
        converter = Converter(dataset_id, dataset)
        return [converter.journey(journey) for journey in list_journeys(dataset.index)]

    @router.get("/datasets/{dataset_id}/objects")
    def search_objects(
        dataset_id: str,
        object_type: Annotated[str | None, Query(alias="type", max_length=MAX_QUERY_LENGTH)] = None,
        q: Annotated[str | None, Query(max_length=MAX_QUERY_LENGTH)] = None,
        limit: Annotated[int, Query(ge=1, le=MAX_SEARCH_LIMIT)] = DEFAULT_SEARCH_LIMIT,
        offset: Annotated[int, Query(ge=0)] = 0,
    ) -> ObjectSearchOut:
        """Einfache Objektsuche nach Typ und Teiltext in ID oder Name, seitenweise."""
        dataset = lookup.dataset(dataset_id)
        converter = Converter(dataset_id, dataset)
        total, rows = dataset.index.search_objects(object_type, q, limit, offset)
        return ObjectSearchOut(total=total, items=[converter.object(row) for row in rows])

    @router.get("/datasets/{dataset_id}/diagnostics")
    def get_diagnostics(
        dataset_id: str,
        category: DiagnosticCategory | None = None,
        severity: Severity | None = None,
    ) -> list[DiagnosticOut]:
        """Diagnosen, optional gefiltert nach Art und Schweregrad."""
        index = lookup.dataset(dataset_id).index
        return [Converter.diagnostic(item) for item in index.diagnostics(category, severity)]

    @router.get("/datasets/{dataset_id}/xml")
    def get_xml_at(
        dataset_id: str,
        file: Annotated[int, Query(ge=1)],
        line: Annotated[int, Query(ge=1)],
        column: Annotated[int, Query(ge=1)] = 1,
    ) -> XmlWindowOut:
        """XML-Ausschnitt um eine Stelle (z. B. einer Diagnose)."""
        dataset = lookup.dataset(dataset_id)
        window = position_xml_window(dataset.index, file, line, column)
        if window is None:
            raise _not_found()
        return Converter(dataset_id, dataset).xml_window(window)

    return router


def object_router(registry: DatasetRegistry) -> APIRouter:
    """Router für Objekte und Elemente: Detail und XML-Ausschnitt."""
    router = APIRouter(prefix="/api")
    lookup = _Lookup(registry)

    @router.get("/objects/{object_id}")
    def get_object(object_id: str) -> ObjectDetailOut:
        """Objektdetail mit Pfad, Frame und Eigenschaften."""
        dataset_id, dataset, element_id = lookup.element(object_id)
        detail = object_detail(dataset.index, element_id)
        if detail is None:
            raise _not_found()
        return Converter(dataset_id, dataset).detail(detail)

    @router.get("/objects/{object_id}/xml")
    def get_object_xml(object_id: str) -> XmlWindowOut:
        """XML-Ausschnitt mit dem markierten Objekt oder Element."""
        dataset_id, dataset, element_id = lookup.element(object_id)
        window = element_xml_window(dataset.index, element_id)
        if window is None:
            raise _not_found()
        return Converter(dataset_id, dataset).xml_window(window)

    return router
