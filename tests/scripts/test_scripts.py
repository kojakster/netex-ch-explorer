"""Tests für die Logik der Skripte (ohne npm, ohne Server, ohne echten Testlauf)."""

from __future__ import annotations

import importlib.util
import json
import os
import socket
import subprocess
import sys
from pathlib import Path
from types import ModuleType

import pytest

from app.core.guide.guide_tested import read_test_record
from tests.support import PROJECT_ROOT, SHA_A, GitRepoFactory

SCRIPTS_DIR = PROJECT_ROOT / "scripts"
# Die Skripte importieren ihr gemeinsames Modul `frontend` aus dem eigenen Ordner.
if str(SCRIPTS_DIR) not in sys.path:
    sys.path.insert(0, str(SCRIPTS_DIR))


def load_script(name: str) -> ModuleType:
    spec = importlib.util.spec_from_file_location(f"scripts_{name}", SCRIPTS_DIR / f"{name}.py")
    assert spec is not None
    assert spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    # Eigener Name, damit z. B. `test` nicht das gleichnamige Paket der Standardbibliothek verdeckt.
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


frontend = load_script("frontend")
start = load_script("start")
test_script = load_script("test")
check = load_script("check")


def touch(path: Path, mtime: float) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("x", encoding="utf-8")
    os.utime(path, (mtime, mtime))


def test_frontend_needs_build_without_dist(tmp_path: Path) -> None:
    assert frontend.frontend_needs_build(tmp_path)


def test_frontend_build_is_current(tmp_path: Path) -> None:
    touch(tmp_path / "src" / "App.tsx", 100)
    touch(tmp_path / "package.json", 100)
    touch(tmp_path / "dist" / "index.html", 200)
    assert not frontend.frontend_needs_build(tmp_path)


def test_frontend_build_is_outdated(tmp_path: Path) -> None:
    touch(tmp_path / "dist" / "index.html", 200)
    touch(tmp_path / "src" / "components" / "Neu.tsx", 300)
    assert frontend.frontend_needs_build(tmp_path)


def test_dependencies_need_install(tmp_path: Path) -> None:
    touch(tmp_path / "package-lock.json", 200)
    assert frontend.dependencies_need_install(tmp_path)
    touch(tmp_path / "node_modules" / ".package-lock.json", 100)
    assert frontend.dependencies_need_install(tmp_path)
    touch(tmp_path / "node_modules" / ".package-lock.json", 300)
    assert not frontend.dependencies_need_install(tmp_path)


@pytest.mark.parametrize("value", ["80", "70000"])
def test_start_rejects_invalid_port(value: str) -> None:
    with pytest.raises(SystemExit):
        start.main(["--port", value])


def test_port_is_free_detects_a_listening_server() -> None:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
        server.bind(("127.0.0.1", 0))
        server.listen()
        port = server.getsockname()[1]
        assert not start.port_is_free(port)
    assert start.port_is_free(port)


def fake_project(tmp_path: Path, make_git_repo: GitRepoFactory) -> Path:
    guide = tmp_path / "guide"
    make_git_repo(guide)
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "settings.json").write_text(
        json.dumps({"guidePath": str(guide)}), encoding="utf-8"
    )
    return tmp_path


def fake_run(returncode: int) -> object:
    def run(command: list[str], **_kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(command, returncode)

    return run


def test_test_script_writes_record_on_success(
    tmp_path: Path, make_git_repo: GitRepoFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = fake_project(tmp_path, make_git_repo)
    monkeypatch.setattr(test_script, "PROJECT_ROOT", project)
    monkeypatch.setattr(test_script.subprocess, "run", fake_run(0))
    assert test_script.main([]) == 0
    record = read_test_record(project / "guide-tested.json")
    assert record is not None
    assert record.guide_commit == SHA_A
    assert record.xsd_commit is None


def test_test_script_keeps_record_on_failure(
    tmp_path: Path, make_git_repo: GitRepoFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = fake_project(tmp_path, make_git_repo)
    monkeypatch.setattr(test_script, "PROJECT_ROOT", project)
    monkeypatch.setattr(test_script.subprocess, "run", fake_run(1))
    assert test_script.main([]) == 1
    assert not (project / "guide-tested.json").exists()


def test_test_script_needs_guide_commit(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> None:
    (tmp_path / "config").mkdir()
    (tmp_path / "config" / "settings.json").write_text(
        json.dumps({"guidePath": str(tmp_path / "fehlt")}), encoding="utf-8"
    )
    monkeypatch.setattr(test_script, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(test_script.subprocess, "run", fake_run(0))
    assert test_script.main([]) == 1
    assert not (tmp_path / "guide-tested.json").exists()


def test_test_script_partial_run_writes_no_record(
    tmp_path: Path, make_git_repo: GitRepoFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    project = fake_project(tmp_path, make_git_repo)
    monkeypatch.setattr(test_script, "PROJECT_ROOT", project)
    monkeypatch.setattr(test_script.subprocess, "run", fake_run(0))
    assert test_script.main(["-k", "config"]) == 0
    assert not (project / "guide-tested.json").exists()


def test_check_hook_detects_unstaged_changes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    assert check._run([check._tool("git"), "init", "-q"], cwd=tmp_path)
    monkeypatch.setattr(check, "PROJECT_ROOT", tmp_path)
    assert check._index_matches_worktree()
    (tmp_path / "neu.txt").write_text("x", encoding="utf-8")
    assert not check._index_matches_worktree()
