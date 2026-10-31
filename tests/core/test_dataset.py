"""Datensatz: Meldungen beim Öffnen, Dateiinhalt, Versionserkennung und Freigabe der Dateien."""

from __future__ import annotations

import sqlite3
import threading
from pathlib import Path

import pytest

from app.core.dataset import FileNote, SourceFile, open_dataset
from app.core.diagnostics import DiagnosticCategory
from app.core.messages import MessageKey, Severity
from app.core.validation.detection import DetectionStatus
from tests.support import FIXTURES_DIR, REF_TARGETS

XML = (FIXTURES_DIR / "ch20_three_stops.xml").read_bytes()


def test_notes_become_file_diagnostics() -> None:
    notes = [
        FileNote("a.xml", Severity.INFO, MessageKey.FILE_NAME_CHANGED, {"original": "a b.xml"}),
        FileNote("z.zip", Severity.ERROR, MessageKey.ZIP_UNREADABLE, {}),
    ]
    dataset = open_dataset([SourceFile("a.xml", XML)], (), REF_TARGETS, notes)
    files = dataset.index.files()
    assert [(f.name, f.readable) for f in files] == [("a.xml", True), ("z.zip", False)]
    found = [
        (d.file_name, d.diagnostic.category, d.diagnostic.key)
        for d in dataset.index.diagnostics(DiagnosticCategory.FILE)
    ]
    assert found == [
        ("a.xml", DiagnosticCategory.FILE, MessageKey.FILE_NAME_CHANGED),
        ("z.zip", DiagnosticCategory.FILE, MessageKey.ZIP_UNREADABLE),
    ]
    assert dataset.detections[2].status is DetectionStatus.UNKNOWN
    assert dataset.read_file(1) == XML
    assert dataset.read_file(2) is None


def test_dataset_without_readable_files_is_still_open() -> None:
    note = FileNote("x.txt", Severity.ERROR, MessageKey.FILE_TYPE_UNSUPPORTED, {})
    dataset = open_dataset([], (), REF_TARGETS, [note])
    assert [f.name for f in dataset.index.files()] == ["x.txt"]
    assert dataset.read_file(1) is None


def test_raw_data_is_read_from_the_file_not_kept_in_memory(tmp_path: Path) -> None:
    path = tmp_path / "a.xml"
    path.write_bytes(XML)
    dataset = open_dataset([SourceFile("a.xml", b"anders", path)], (), REF_TARGETS)
    assert dataset.read_file(1) == XML
    path.write_bytes(b"neu")
    assert dataset.read_file(1) == b"neu"
    path.unlink()
    assert dataset.read_file(1) is None


def test_release_runs_once_and_close_releases() -> None:
    calls: list[str] = []
    dataset = open_dataset(
        [SourceFile("a.xml", XML)], (), REF_TARGETS, release=lambda: calls.append("x")
    )
    dataset.close()
    dataset.close()
    assert calls == ["x"]


def test_close_without_release_callback() -> None:
    open_dataset([SourceFile("a.xml", XML)], (), REF_TARGETS).close()


def test_close_waits_for_running_requests() -> None:
    calls: list[str] = []
    dataset = open_dataset(
        [SourceFile("a.xml", XML)], (), REF_TARGETS, release=lambda: calls.append("x")
    )
    assert dataset.acquire()
    assert dataset.acquire()
    dataset.close()
    assert calls == []
    assert dataset.index.files()  # der Index ist noch benutzbar
    dataset.release()
    assert calls == []
    dataset.release()
    assert calls == ["x"]
    with pytest.raises(sqlite3.ProgrammingError):
        dataset.index.files()


def test_closing_dataset_cannot_be_acquired() -> None:
    dataset = open_dataset([SourceFile("a.xml", XML)], (), REF_TARGETS)
    assert dataset.acquire()
    dataset.close()
    assert not dataset.acquire()
    dataset.release()


def test_close_and_release_from_threads_finish_once() -> None:
    calls: list[str] = []
    dataset = open_dataset(
        [SourceFile("a.xml", XML)], (), REF_TARGETS, release=lambda: calls.append("x")
    )
    assert dataset.acquire()
    closer = threading.Thread(target=dataset.close)
    closer.start()
    closer.join()
    assert calls == []
    dataset.release()
    assert calls == ["x"]
