from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import load_config
from app.core.guide.mapping import MappingRow, MappingSheet, MappingTable
from app.core.guide.status import GuideRevision, GuideStatus, GuideTestState
from app.core.messages import Issue, MessageKey, Severity
from app.server.app import Runtime, create_app, load_runtime
from app.server.security import CONTENT_SECURITY_POLICY
from tests.support import SHA_A, SHA_B

BASE_URL = "http://127.0.0.1"


def runtime(tmp_path: Path) -> Runtime:
    guide = GuideStatus(
        path=tmp_path / "guide",
        found=True,
        revision=GuideRevision(branch="next", commit=SHA_A, xsd_commit=SHA_B),
        xsd_present=True,
        test_state=GuideTestState.DIFFERS,
        tested_commit=SHA_B,
        mapping=MappingTable(
            sheets={"StopUse": MappingSheet("StopUse", 3, (MappingRow(4, {"Value": "access"}),))}
        ),
        issues=(
            Issue(Severity.INFO, MessageKey.GUIDE_TESTED_DIFFERS, {"testedCommit": "bbbbbbb"}),
        ),
    )
    return Runtime(config=load_config(tmp_path), guide=guide)


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    return TestClient(create_app(runtime(tmp_path), None), base_url=BASE_URL)


def test_guide_endpoint(client: TestClient, tmp_path: Path) -> None:
    response = client.get("/api/guide")
    assert response.status_code == 200
    assert response.json() == {
        "path": str(tmp_path / "guide"),
        "found": True,
        "branch": "next",
        "commit": SHA_A,
        "xsdCommit": SHA_B,
        "xsdPresent": True,
        "testState": "differs",
        "testedCommit": SHA_B,
        "mappingSheets": [{"name": "StopUse", "headerRow": 3, "rows": 1}],
        "issues": [
            {
                "severity": "info",
                "key": "guide.tested_differs",
                "params": {"testedCommit": "bbbbbbb"},
            }
        ],
    }
    assert response.headers["Cache-Control"] == "no-store"


def test_app_endpoint(client: TestClient) -> None:
    data = client.get("/api/app").json()
    assert data["language"] == "de-CH"
    assert data["languages"] == ["de-CH", "en"]
    assert data["frameColors"][0] == {
        "key": "TimetableFrame",
        "background": "#0057B8",
        "text": "#FFFFFF",
    }
    assert "SiteFacilitySet" in data["notRelevantElements"]
    assert data["features"] == ["guide_status", "frame_legend", "language_switch", "help_page"]
    assert data["severities"] == ["error", "warning", "info"]
    assert {
        "id": "xsd",
        "status": "not_implemented",
        "sources": ["xsd/xsd/NeTEx_publication.xsd"],
    } in data["checks"]
    # Leerer Projektordner: alle drei Einstellungsdateien fehlen.
    assert [issue["key"] for issue in data["issues"]] == ["config.file_missing"] * 3


def test_security_headers(client: TestClient) -> None:
    headers = client.get("/api/guide").headers
    assert headers["Content-Security-Policy"] == CONTENT_SECURITY_POLICY
    assert headers["X-Content-Type-Options"] == "nosniff"
    assert headers["X-Frame-Options"] == "DENY"
    assert headers["Referrer-Policy"] == "no-referrer"


def test_unknown_route_uses_error_format(client: TestClient) -> None:
    response = client.get("/api/gibtsnicht")
    assert response.status_code == 404
    assert response.json() == {"error": {"key": "error.not_found", "params": {}}}


def test_wrong_method_uses_error_format(client: TestClient) -> None:
    response = client.post("/api/guide")
    assert response.status_code == 405
    assert response.json() == {"error": {"key": "error.method_not_allowed", "params": {}}}


def test_foreign_host_is_rejected(tmp_path: Path) -> None:
    client = TestClient(create_app(runtime(tmp_path), None), base_url="http://evil.example")
    assert client.get("/api/guide").status_code == 400


def test_localhost_is_accepted(tmp_path: Path) -> None:
    client = TestClient(create_app(runtime(tmp_path), None), base_url="http://localhost:8765")
    assert client.get("/api/guide").status_code == 200


def test_internal_error_hides_details(tmp_path: Path) -> None:
    app = create_app(runtime(tmp_path), None)

    def fail() -> None:
        message = "geheimes Detail"
        raise RuntimeError(message)

    app.add_api_route("/api/fail", fail)
    client = TestClient(app, base_url=BASE_URL, raise_server_exceptions=False)
    response = client.get("/api/fail")
    assert response.status_code == 500
    assert response.json() == {"error": {"key": "error.internal", "params": {}}}
    assert "geheim" not in response.text
    assert response.headers["Content-Security-Policy"] == CONTENT_SECURITY_POLICY
    assert response.headers["Cache-Control"] == "no-store"


def test_validation_error_uses_error_format(tmp_path: Path) -> None:
    app = create_app(runtime(tmp_path), None)

    def needs_number(value: int) -> int:
        return value

    app.add_api_route("/api/number", needs_number)
    response = TestClient(app, base_url=BASE_URL).get("/api/number", params={"value": "x"})
    assert response.status_code == 422
    assert response.json() == {"error": {"key": "error.invalid_request", "params": {}}}


def test_serves_frontend(tmp_path: Path) -> None:
    dist = tmp_path / "dist"
    dist.mkdir()
    (dist / "index.html").write_text("<!doctype html><title>x</title>", encoding="utf-8")
    client = TestClient(create_app(runtime(tmp_path), dist), base_url=BASE_URL)
    response = client.get("/")
    assert response.status_code == 200
    assert "<title>x</title>" in response.text
    assert response.headers["Content-Security-Policy"] == CONTENT_SECURITY_POLICY
    assert client.get("/api/guide").status_code == 200
    assert client.get("/../config/settings.json").status_code == 404


def test_load_runtime_uses_project_config(tmp_path: Path) -> None:
    loaded = load_runtime(tmp_path)
    assert (
        loaded.config.settings.guide_path
        == (tmp_path / "../netexRealisationGuideSwitzerland").resolve()
    )
    assert loaded.guide.found is loaded.config.settings.guide_path.is_dir()
