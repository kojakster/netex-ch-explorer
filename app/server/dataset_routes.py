"""Endpunkte für Datensätze, Objekte, Fahrten, Diagnosen und XML-Ausschnitte (docs/api.md)."""

from __future__ import annotations

from collections.abc import Iterator
from functools import partial
from typing import Annotated, Final, NamedTuple

from fastapi import APIRouter, Depends, File, HTTPException, Query, Request, Response, UploadFile
from starlette.status import (
    HTTP_204_NO_CONTENT,
    HTTP_404_NOT_FOUND,
    HTTP_413_CONTENT_TOO_LARGE,
)

from app.core.dataset import Dataset, SourceFile, open_dataset
from app.core.diagnostics import DiagnosticCategory
from app.core.explorer import element_xml_window, object_detail, position_xml_window
from app.core.guide.examples import Example, example_path
from app.core.intake import Upload, receive
from app.core.messages import Severity
from app.core.projection.journey_view import build_journey_view, is_journey
from app.core.projection.journeys import list_journeys
from app.core.provenance import provenance_chain
from app.server.dataset_schemas import (
    ChainLinkOut,
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
from app.server.journey_schemas import JourneyConverter, JourneyViewOut
from app.server.runtime import Runtime

MAX_SEARCH_LIMIT: Final = 200
DEFAULT_SEARCH_LIMIT: Final = 50
MAX_QUERY_LENGTH: Final = 200
# Obergrenzen, damit sehr grosse Zahlen eine Eingabefehler-Antwort ergeben (SQLite: 64 Bit).
MAX_NUMBER: Final = 1_000_000_000


def _not_found() -> HTTPException:
    return HTTPException(status_code=HTTP_404_NOT_FOUND)


class _OpenDataset(NamedTuple):
    """Ein für die Dauer der Anfrage festgehaltener Datensatz mit seiner ID."""

    dataset_id: str
    dataset: Dataset


class _ElementTarget(NamedTuple):
    """Ziel einer Objekt-ID: Datensatz-ID, Datensatz und Elementnummer."""

    dataset_id: str
    dataset: Dataset
    element_id: int


def _registry_of(request: Request) -> DatasetRegistry:
    registry = request.app.state.registry
    if not isinstance(registry, DatasetRegistry):
        raise TypeError("Die Anwendung hat keine Liste der offenen Datensätze.")
    return registry


def _leased_dataset(request: Request, dataset_id: str) -> Iterator[_OpenDataset]:
    """Abhängigkeit: der Datensatz zum Pfadparameter `dataset_id`, für die Anfrage festgehalten.

    Ein gleichzeitiges Schliessen wirkt erst nach der Anfrage. Unbekannte oder ungültige IDs
    ergeben 404.
    """
    dataset = _registry_of(request).acquire(dataset_id)
    if dataset is None:
        raise _not_found()
    try:
        yield _OpenDataset(dataset_id, dataset)
    finally:
        dataset.release()


def _leased_element(request: Request, object_id: str) -> Iterator[_ElementTarget]:
    """Abhängigkeit: Datensatz (festgehalten) und Elementnummer zum Pfadparameter `object_id`."""
    parsed = parse_object_id(object_id)
    if parsed is None:
        raise _not_found()
    dataset_id, element_id = parsed
    dataset = _registry_of(request).acquire(dataset_id)
    if dataset is None:
        raise _not_found()
    try:
        yield _ElementTarget(dataset_id, dataset, element_id)
    finally:
        dataset.release()


LeasedDataset = Annotated[_OpenDataset, Depends(_leased_dataset)]
LeasedElement = Annotated[_ElementTarget, Depends(_leased_element)]


def _converter(runtime: Runtime, dataset_id: str, dataset: Dataset) -> Converter:
    return Converter(dataset_id, dataset, runtime.links, runtime.guide.revision.commit)


def lifecycle_router(runtime: Runtime, registry: DatasetRegistry) -> APIRouter:
    """Router für eigene Dateien: hochladen, validieren, schliessen."""
    router = APIRouter(prefix="/api")
    not_relevant = runtime.config.not_relevant_elements
    ref_targets = runtime.config.ref_targets

    @router.post("/datasets/upload")
    def upload_files(files: Annotated[list[UploadFile], File()]) -> DatasetOut:
        """Öffnet eigene Dateien aus dem Dialog „Datei öffnen“: XML-Dateien oder ZIP (multipart).

        Die Dateien landen nur in `work/` und werden beim Schliessen des Datensatzes gelöscht.
        Abgewiesene Dateien erscheinen als Diagnosen der Art `file`.
        """
        limits = runtime.config.settings.zip_limits
        if len(files) > limits.max_files:
            raise HTTPException(status_code=HTTP_413_CONTENT_TOO_LARGE)
        uploads = [
            Upload(item.filename or "", item.file.read(limits.max_total_bytes + 1))
            for item in files
        ]
        session = runtime.workspace.new_session()
        dataset: Dataset | None = None
        try:
            received = receive(uploads, session, limits)
            dataset = open_dataset(
                received.sources,
                not_relevant,
                ref_targets,
                received.notes,
                partial(runtime.workspace.remove_session, session),
            )
        finally:
            if dataset is None:
                runtime.workspace.remove_session(session)
        dataset_id = registry.add(dataset)
        return _converter(runtime, dataset_id, dataset).dataset()

    @router.delete("/datasets/{dataset_id}", status_code=HTTP_204_NO_CONTENT)
    def close_dataset(dataset_id: str) -> Response:
        """Schliesst den Datensatz und löscht seine Dateien in `work/`."""
        if not registry.remove(dataset_id):
            raise _not_found()
        return Response(status_code=HTTP_204_NO_CONTENT)

    @router.post("/datasets/{dataset_id}/validate")
    def validate_dataset(target: LeasedDataset) -> DatasetOut:
        """Startet die Validierung (nur als CH 2.0 erkannte Dateien) und liefert das Ergebnis."""
        dataset_id, dataset = target
        runtime.engine.validate(dataset)
        return _converter(runtime, dataset_id, dataset).dataset()

    return router


def dataset_router(runtime: Runtime, registry: DatasetRegistry) -> APIRouter:
    """Router für Datensätze: öffnen, Übersicht, Fahrten, Objektsuche, Diagnosen, XML an Stelle."""
    router = APIRouter(prefix="/api")
    examples = [Example(status.name, status.title) for status in runtime.guide.examples]
    not_relevant = runtime.config.not_relevant_elements
    ref_targets = runtime.config.ref_targets

    def converter(dataset_id: str, dataset: Dataset) -> Converter:
        return _converter(runtime, dataset_id, dataset)

    @router.post("/datasets")
    def open_example(request: OpenDatasetIn) -> DatasetOut:
        """Öffnet ein Beispiel des Guides (nur Namen aus der Beispielliste, nie Pfade)."""
        path = example_path(runtime.config.settings.guide_path, request.example, examples)
        if path is None:
            raise _not_found()
        source = SourceFile(request.example, path.read_bytes(), path)
        dataset = open_dataset([source], not_relevant, ref_targets)
        dataset_id = registry.add(dataset)
        return converter(dataset_id, dataset).dataset()

    @router.get("/datasets/{dataset_id}")
    def get_dataset(target: LeasedDataset) -> DatasetOut:
        """Übersicht über einen geöffneten Datensatz."""
        return converter(*target).dataset()

    @router.get("/datasets/{dataset_id}/journeys")
    def get_journeys(target: LeasedDataset) -> list[JourneyOut]:
        """Liste der Fahrten."""
        dataset_id, dataset = target
        journeys = converter(dataset_id, dataset)
        return [journeys.journey(journey) for journey in list_journeys(dataset.index)]

    @router.get("/datasets/{dataset_id}/objects")
    def search_objects(
        target: LeasedDataset,
        object_type: Annotated[str | None, Query(alias="type", max_length=MAX_QUERY_LENGTH)] = None,
        q: Annotated[str | None, Query(max_length=MAX_QUERY_LENGTH)] = None,
        limit: Annotated[int, Query(ge=1, le=MAX_SEARCH_LIMIT)] = DEFAULT_SEARCH_LIMIT,
        offset: Annotated[int, Query(ge=0, le=MAX_NUMBER)] = 0,
    ) -> ObjectSearchOut:
        """Einfache Objektsuche nach Typ und Teiltext in ID oder Name, seitenweise."""
        dataset_id, dataset = target
        objects = converter(dataset_id, dataset)
        total, rows = dataset.index.search_objects(object_type, q, limit, offset)
        return ObjectSearchOut(total=total, items=[objects.object(row) for row in rows])

    @router.get("/datasets/{dataset_id}/diagnostics")
    def get_diagnostics(
        target: LeasedDataset,
        category: DiagnosticCategory | None = None,
        severity: Severity | None = None,
    ) -> list[DiagnosticOut]:
        """Diagnosen, optional gefiltert nach Art und Schweregrad."""
        dataset_id, dataset = target
        diagnostics = converter(dataset_id, dataset)
        items = dataset.index.diagnostics(category, severity)
        return [diagnostics.diagnostic(item) for item in items]

    @router.get("/datasets/{dataset_id}/xml")
    def get_xml_at(
        target: LeasedDataset,
        file: Annotated[int, Query(ge=1, le=MAX_NUMBER)],
        line: Annotated[int, Query(ge=1, le=MAX_NUMBER)],
        column: Annotated[int, Query(ge=1, le=MAX_NUMBER)] = 1,
    ) -> XmlWindowOut:
        """XML-Ausschnitt um eine Stelle (z. B. einer Diagnose)."""
        dataset_id, dataset = target
        window = position_xml_window(dataset.index, file, line, column)
        if window is None:
            raise _not_found()
        return converter(dataset_id, dataset).xml_window(window)

    return router


def object_router() -> APIRouter:
    """Router für Objekte und Elemente: Detail, Herkunftskette und XML-Ausschnitt."""
    router = APIRouter(prefix="/api")

    @router.get("/objects/{object_id}")
    def get_object(target: LeasedElement) -> ObjectDetailOut:
        """Objektdetail mit Pfad, Frame und Eigenschaften."""
        dataset_id, dataset, element_id = target
        detail = object_detail(dataset.index, element_id)
        if detail is None:
            raise _not_found()
        return Converter(dataset_id, dataset).detail(detail)

    @router.get("/objects/{object_id}/provenance")
    def get_provenance(target: LeasedElement) -> list[ChainLinkOut]:
        """Herkunftskette: Frame, enthaltende Objekte, Angabe, bei Referenzen das Ziel."""
        dataset_id, dataset, element_id = target
        links = provenance_chain(dataset.index, element_id)
        if links is None:
            raise _not_found()
        return Converter(dataset_id, dataset).chain(links)

    @router.get("/objects/{object_id}/xml")
    def get_object_xml(target: LeasedElement) -> XmlWindowOut:
        """XML-Ausschnitt mit dem markierten Objekt oder Element."""
        dataset_id, dataset, element_id = target
        window = element_xml_window(dataset.index, element_id)
        if window is None:
            raise _not_found()
        return Converter(dataset_id, dataset).xml_window(window)

    return router


def journey_router(runtime: Runtime) -> APIRouter:
    """Router der Fahrtansicht: `GET /api/journeys/{id}`."""
    router = APIRouter(prefix="/api")

    @router.get("/journeys/{object_id}")
    def get_journey(target: LeasedElement) -> JourneyViewOut:
        """Fahrtansicht einer `ServiceJourney` (oder `TemplateServiceJourney`)."""
        dataset_id, dataset, element_id = target
        element = dataset.index.element(element_id)
        if element is None or not is_journey(element):
            raise _not_found()
        view = build_journey_view(dataset.index, element, runtime.guide.mapping)
        converter = JourneyConverter(Converter(dataset_id, dataset), runtime.guide.revision.commit)
        return converter.journey(view)

    return router
