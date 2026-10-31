"""Beim Start geladener Zustand: Beispiele werden im Hintergrund geprüft."""

from __future__ import annotations

import logging
from dataclasses import replace
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from app.core.config import load_config
from app.core.dataset import Dataset
from app.core.guide.examples import ExampleResult
from app.core.guide.status import inspect_guide
from app.core.validation.result import ValidationSummary
from app.server.app import create_app
from app.server.runtime import Runtime
from tests.support import PROJECT_ROOT, REF_TARGETS

BASE_URL = "http://127.0.0.1"


def pending_runtime(synthetic_guide: Path, tmp_path: Path, *, with_record: bool = True) -> Runtime:
    config = load_config(PROJECT_ROOT)
    config = replace(config, settings=replace(config.settings, guide_path=synthetic_guide))
    record = tmp_path / "t.json"
    guide = inspect_guide(synthetic_guide, record, REF_TARGETS, defer_examples=True)
    return Runtime(config, guide, tmp_path / "work", record if with_record else None)


def test_guide_endpoint_while_examples_are_pending(synthetic_guide: Path, tmp_path: Path) -> None:
    runtime = pending_runtime(synthetic_guide, tmp_path)
    client = TestClient(create_app(runtime, None), base_url=BASE_URL)
    data = client.get("/api/guide").json()
    assert data["examplesReady"] is False
    assert data["xsdLoaded"] is False
    assert [e["result"] for e in data["examples"]] == [None, None, None]
    assert data["examples"][2]["title"] == "Synthetische Fahrt"
    # Die Beispiele lassen sich schon öffnen.
    assert client.post("/api/datasets", json={"example": "ch20_three_stops.xml"}).status_code == 200
    runtime.complete_examples()
    data = client.get("/api/guide").json()
    assert data["examplesReady"] is True
    assert {e["name"]: e["result"] for e in data["examples"]}["broken_xml.xml"] == "unreadable"


def test_background_thread_completes_the_examples(synthetic_guide: Path, tmp_path: Path) -> None:
    runtime = pending_runtime(synthetic_guide, tmp_path)
    runtime.start_background().join(timeout=60)
    assert runtime.guide.examples_ready


def test_background_failure_is_logged_and_does_not_stop_the_server(
    synthetic_guide: Path,
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    runtime = pending_runtime(synthetic_guide, tmp_path)

    def explode() -> None:
        raise OSError("kaputt")

    monkeypatch.setattr(runtime, "complete_examples", explode)
    with caplog.at_level(logging.ERROR):
        runtime.start_background().join(timeout=10)
    assert not runtime.guide.examples_ready
    assert "Prüfung der Beispiele fehlgeschlagen" in caplog.text


def test_without_test_record_path_nothing_is_completed(
    synthetic_guide: Path, tmp_path: Path
) -> None:
    runtime = pending_runtime(synthetic_guide, tmp_path, with_record=False)
    runtime.complete_examples()
    assert not runtime.guide.examples_ready


def test_program_error_in_the_check_still_finishes_the_examples(
    synthetic_guide: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    runtime = pending_runtime(synthetic_guide, tmp_path)

    def explode(_dataset: Dataset) -> ValidationSummary:
        raise ValueError("Programmfehler")

    monkeypatch.setattr(runtime.engine, "validate", explode)
    with pytest.raises(ValueError, match="Programmfehler"):
        runtime.complete_examples()
    assert runtime.guide.examples_ready
    assert {e.result for e in runtime.guide.examples} == {ExampleResult.CHECK_FAILED}
