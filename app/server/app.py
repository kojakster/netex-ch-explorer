"""FastAPI-Anwendung: lokale JSON-Schnittstelle und Auslieferung der gebauten Oberfläche."""

from __future__ import annotations

from collections.abc import Awaitable, Callable
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from fastapi import APIRouter, FastAPI, Request, Response
from fastapi.staticfiles import StaticFiles
from starlette.middleware.trustedhost import TrustedHostMiddleware

from app.core.config import SUPPORTED_LANGUAGES, AppConfig, load_config
from app.core.guide.guide_tested import TEST_RECORD_FILE
from app.core.guide.status import GuideStatus, inspect_guide
from app.server.errors import register_error_handlers
from app.server.schemas import AppInfoOut, GuideOut
from app.server.security import ALLOWED_HOSTS, NO_STORE, SECURITY_HEADERS

FRONTEND_DIST: Final = Path("app") / "frontend" / "dist"


@dataclass(frozen=True)
class Runtime:
    """Beim Start geladener Zustand: Einstellungen und Guide-Status."""

    config: AppConfig
    guide: GuideStatus


def load_runtime(project_root: Path) -> Runtime:
    """Lädt Einstellungen und untersucht den Guide-Klon."""
    config = load_config(project_root)
    guide = inspect_guide(config.settings.guide_path, project_root / TEST_RECORD_FILE)
    return Runtime(config=config, guide=guide)


def create_app(runtime: Runtime, frontend_dist: Path | None) -> FastAPI:
    """Erzeugt die Anwendung.

    Args:
        runtime: Beim Start geladener Zustand.
        frontend_dist: Ordner der gebauten Oberfläche; `None` oder fehlend = nur Schnittstelle.
    """
    app = FastAPI(
        title="NeTEx CH Explorer",
        # Keine Swagger-Oberfläche: sie lädt Ressourcen aus dem Internet.
        docs_url=None,
        redoc_url=None,
        openapi_url=None,
    )
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=list(ALLOWED_HOSTS))
    app.middleware("http")(_add_security_headers)
    register_error_handlers(app)
    app.include_router(_api_router(runtime))
    if frontend_dist is not None and frontend_dist.is_dir():
        app.mount("/", StaticFiles(directory=frontend_dist, html=True), name="frontend")
    return app


def _api_router(runtime: Runtime) -> APIRouter:
    guide = GuideOut.from_status(runtime.guide)
    app_info = AppInfoOut.from_config(runtime.config, SUPPORTED_LANGUAGES)
    router = APIRouter(prefix="/api")

    @router.get("/guide")
    def get_guide() -> GuideOut:
        """Guide-Status für die Guide-Status-Box."""
        return guide

    @router.get("/app")
    def get_app_info() -> AppInfoOut:
        """Farben, Grau-Liste, Funktionen, Prüfschritte und Schweregrade."""
        return app_info

    return router


async def _add_security_headers(
    request: Request, call_next: Callable[[Request], Awaitable[Response]]
) -> Response:
    response = await call_next(request)
    response.headers.update(SECURITY_HEADERS)
    if request.url.path.startswith("/api/"):
        response.headers.update(NO_STORE)
    return response
