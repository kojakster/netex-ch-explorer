from __future__ import annotations

import json
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import load_config
from app.core.features import Feature
from app.core.guide.mapping import MappingRow, MappingSheet, MappingTable
from app.core.guide.status import GuideRevision, GuideStatus, GuideTestState
from app.core.messages import Issue, MessageKey, Severity
from app.core.validation.steps import CHECK_STEPS
from app.server.app import create_app
from app.server.runtime import Runtime, load_runtime
from app.server.security import CONTENT_SECURITY_POLICY
from tests.support import PROJECT_ROOT, SHA_A, SHA_B

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
    return Runtime(config=load_config(tmp_path), guide=guide, work_dir=tmp_path / "work")


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
        "commitDate": None,
        "xsdCommit": SHA_B,
        "xsdPresent": True,
        "testState": "differs",
        "testedCommit": SHA_B,
        "mappingSheets": [{"name": "StopUse", "headerRow": 3, "rows": 1}],
        "examples": [],
        "examplesReady": True,
        "xsdLoaded": False,
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
    assert data["features"] == [str(feature) for feature in Feature]
    assert data["severities"] == ["error", "warning", "info"]
    assert {
        "id": "xsd",
        "status": "performed",
        "sources": ["xsd/xsd/NeTEx_publication.xsd"],
    } in data["checks"]
    # Leerer Projektordner: alle vier Einstellungsdateien fehlen.
    assert [issue["key"] for issue in data["issues"]] == ["config.file_missing"] * 4


def test_help_data_shows_the_current_config_and_all_checks(tmp_path: Path) -> None:
    """Abnahme Phase 5: Die Hilfeseite zeigt die Farben und die Grau-Liste aus `config/` sowie
    alle durchgeführten und nicht durchgeführten Prüfungen der Liste der Prüfschritte."""
    stub = runtime(tmp_path)
    real = Runtime(config=load_config(PROJECT_ROOT), guide=stub.guide, work_dir=tmp_path / "work")
    data = TestClient(create_app(real, None), base_url=BASE_URL).get("/api/app").json()
    colors = json.loads((PROJECT_ROOT / "config" / "frame-colors.json").read_text(encoding="utf-8"))
    assert {
        color["key"]: (color["background"], color["text"]) for color in data["frameColors"]
    } == {key: (value["background"], value["text"]) for key, value in colors.items()}
    gray = json.loads(
        (PROJECT_ROOT / "config" / "not-relevant-elements.json").read_text(encoding="utf-8")
    )
    assert data["notRelevantElements"] == gray["elements"]
    assert [(check["id"], check["status"]) for check in data["checks"]] == [
        (step.id, str(step.status)) for step in CHECK_STEPS
    ]
    statuses = {check["status"] for check in data["checks"]}
    assert "performed" in statuses
    assert statuses - {"performed"}, "mindestens eine nicht durchgeführte Prüfung"
    assert data["issues"] == []


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


def test_origin_check_uses_the_port_the_server_runs_on(tmp_path: Path) -> None:
    """Mit `start.py --port` weicht der Port von `config/settings.json` ab (E2E-Test, Phase 5)."""
    app = create_app(runtime(tmp_path), None, port=9000)
    client = TestClient(app, base_url="http://127.0.0.1:9000")
    own = {"Origin": "http://127.0.0.1:9000"}
    configured = {"Origin": "http://127.0.0.1:8765"}
    assert client.delete("/api/datasets/abc", headers=own).status_code == 404
    assert client.delete("/api/datasets/abc", headers=configured).status_code == 403


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


def test_each_port_has_its_own_work_folder(tmp_path: Path) -> None:
    """Ein zweiter Server (anderer Port) darf die Arbeitsdateien des ersten nie löschen."""
    first = load_runtime(tmp_path, port=8765)
    second = load_runtime(tmp_path, port=8766)
    assert first.workspace.root == tmp_path / "work" / "8765"
    assert second.workspace.root == tmp_path / "work" / "8766"
    session = first.workspace.new_session()
    create_app(second, None, port=8766)
    assert session.is_dir()
    assert load_runtime(tmp_path).workspace.root == tmp_path / "work" / "8765"
