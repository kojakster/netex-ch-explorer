"""Einheitliches Fehlerformat ohne interne Details: `{"error": {"key": …, "params": {…}}}`."""

from __future__ import annotations

import logging
from enum import StrEnum
from http import HTTPStatus

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException
from starlette.status import HTTP_413_CONTENT_TOO_LARGE

from app.server.security import NO_STORE, SECURITY_HEADERS

logger = logging.getLogger(__name__)


class ErrorKey(StrEnum):
    """Übersetzungsschlüssel der Fehlerantworten; ein Test prüft die Sprachdateien."""

    NOT_FOUND = "error.not_found"
    METHOD_NOT_ALLOWED = "error.method_not_allowed"
    INVALID_REQUEST = "error.invalid_request"
    PAYLOAD_TOO_LARGE = "error.payload_too_large"
    FORBIDDEN_ORIGIN = "error.forbidden_origin"
    HTTP = "error.http"
    INTERNAL = "error.internal"


_KEYS_BY_STATUS: dict[int, ErrorKey] = {
    HTTPStatus.NOT_FOUND: ErrorKey.NOT_FOUND,
    HTTPStatus.METHOD_NOT_ALLOWED: ErrorKey.METHOD_NOT_ALLOWED,
    HTTP_413_CONTENT_TOO_LARGE: ErrorKey.PAYLOAD_TOO_LARGE,
}


def error_response(status: int, key: ErrorKey) -> JSONResponse:
    """Baut eine Fehlerantwort im einheitlichen Format.

    Die Sicherheitsheader stehen direkt hier, weil Antworten auf Programmfehler ausserhalb der
    Middleware entstehen.
    """
    return JSONResponse(
        status_code=status,
        content={"error": {"key": key, "params": {}}},
        headers={**SECURITY_HEADERS, **NO_STORE},
    )


async def _http_error(_request: Request, exc: Exception) -> JSONResponse:
    status = exc.status_code if isinstance(exc, StarletteHTTPException) else 500
    return error_response(status, _KEYS_BY_STATUS.get(status, ErrorKey.HTTP))


async def _validation_error(_request: Request, _exc: Exception) -> JSONResponse:
    return error_response(HTTPStatus.UNPROCESSABLE_ENTITY, ErrorKey.INVALID_REQUEST)


async def _internal_error(request: Request, exc: Exception) -> JSONResponse:
    # Programmfehler werden protokolliert, aber nie mit Details an den Client gegeben.
    logger.error("Unerwarteter Fehler bei %s %s", request.method, request.url.path, exc_info=exc)
    return error_response(HTTPStatus.INTERNAL_SERVER_ERROR, ErrorKey.INTERNAL)


def register_error_handlers(app: FastAPI) -> None:
    """Registriert die Fehlerbehandlung für HTTP-, Eingabe- und Programmfehler."""
    app.add_exception_handler(StarletteHTTPException, _http_error)
    app.add_exception_handler(RequestValidationError, _validation_error)
    app.add_exception_handler(Exception, _internal_error)
