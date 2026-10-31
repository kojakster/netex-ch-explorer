from __future__ import annotations

from pathlib import Path

import pytest

from app.core.guide.git import GitHead, GitReadError, find_git_dir, read_head
from tests.support import SHA_A, SHA_B, GitRepoFactory


def test_loose_ref(tmp_path: Path, make_git_repo: GitRepoFactory) -> None:
    git_dir = make_git_repo(tmp_path)
    assert find_git_dir(tmp_path) == git_dir
    assert read_head(git_dir) == GitHead(branch="next", commit=SHA_A)


def test_packed_ref(tmp_path: Path, make_git_repo: GitRepoFactory) -> None:
    git_dir = make_git_repo(tmp_path, commit=SHA_B, packed=True)
    assert read_head(git_dir) == GitHead(branch="next", commit=SHA_B)


def test_detached_head(tmp_path: Path, make_git_repo: GitRepoFactory) -> None:
    git_dir = make_git_repo(tmp_path, branch=None, commit=SHA_B)
    assert read_head(git_dir) == GitHead(branch=None, commit=SHA_B)


def test_branch_without_commit(tmp_path: Path, make_git_repo: GitRepoFactory) -> None:
    git_dir = make_git_repo(tmp_path, commit=None)
    assert read_head(git_dir) == GitHead(branch="next", commit=None)


def test_no_git_dir(tmp_path: Path) -> None:
    assert find_git_dir(tmp_path) is None


def test_gitdir_file_of_submodule(tmp_path: Path, make_git_repo: GitRepoFactory) -> None:
    module_dir = make_git_repo(tmp_path / "modules" / "xsd", branch=None, commit=SHA_B)
    work_tree = tmp_path / "work" / "xsd"
    work_tree.mkdir(parents=True)
    (work_tree / ".git").write_text("gitdir: ../../modules/xsd/.git\n", encoding="utf-8")
    assert find_git_dir(work_tree) == module_dir.resolve()
    assert read_head(module_dir).commit == SHA_B


def test_gitdir_file_with_absolute_path(tmp_path: Path, make_git_repo: GitRepoFactory) -> None:
    module_dir = make_git_repo(tmp_path / "module")
    (tmp_path / "work").mkdir()
    (tmp_path / "work" / ".git").write_text(f"gitdir: {module_dir}\n", encoding="utf-8")
    assert find_git_dir(tmp_path / "work") == module_dir


@pytest.mark.parametrize("content", ["nonsense", "gitdir: does/not/exist"])
def test_invalid_gitdir_file(tmp_path: Path, content: str) -> None:
    (tmp_path / ".git").write_text(content, encoding="utf-8")
    with pytest.raises(GitReadError):
        find_git_dir(tmp_path)


def test_worktree_uses_common_dir(tmp_path: Path, make_git_repo: GitRepoFactory) -> None:
    main_git = make_git_repo(tmp_path / "main", branch="feature", commit=SHA_B, packed=True)
    worktree_git = main_git / "worktrees" / "wt"
    worktree_git.mkdir(parents=True)
    (worktree_git / "HEAD").write_text("ref: refs/heads/feature\n", encoding="utf-8")
    (worktree_git / "commondir").write_text("../..\n", encoding="utf-8")
    assert read_head(worktree_git) == GitHead(branch="feature", commit=SHA_B)


def test_symbolic_ref_is_followed(tmp_path: Path, make_git_repo: GitRepoFactory) -> None:
    git_dir = make_git_repo(tmp_path, branch="main")
    (git_dir / "HEAD").write_text("ref: refs/heads/alias\n", encoding="utf-8")
    (git_dir / "refs" / "heads" / "alias").write_text("ref: refs/heads/main\n", encoding="utf-8")
    assert read_head(git_dir) == GitHead(branch="alias", commit=SHA_A)


def test_symbolic_ref_loop_is_rejected(tmp_path: Path, make_git_repo: GitRepoFactory) -> None:
    git_dir = make_git_repo(tmp_path, branch="loop")
    (git_dir / "refs" / "heads" / "loop").write_text("ref: refs/heads/loop\n", encoding="utf-8")
    with pytest.raises(GitReadError):
        read_head(git_dir)


def test_non_branch_ref(tmp_path: Path, make_git_repo: GitRepoFactory) -> None:
    git_dir = make_git_repo(tmp_path, branch="x")
    (git_dir / "HEAD").write_text("ref: refs/remotes/origin/next\n", encoding="utf-8")
    assert read_head(git_dir) == GitHead(branch=None, commit=None)


@pytest.mark.parametrize(
    "head",
    ["kaputt", "ref: ../../etc/passwd", "ref: refs/../../x", "ref: /refs/heads/x", "abc123"],
)
def test_invalid_head(tmp_path: Path, make_git_repo: GitRepoFactory, head: str) -> None:
    git_dir = make_git_repo(tmp_path)
    (git_dir / "HEAD").write_text(head, encoding="utf-8")
    with pytest.raises(GitReadError):
        read_head(git_dir)


def test_invalid_loose_ref(tmp_path: Path, make_git_repo: GitRepoFactory) -> None:
    git_dir = make_git_repo(tmp_path)
    (git_dir / "refs" / "heads" / "next").write_text("not-a-sha", encoding="utf-8")
    with pytest.raises(GitReadError):
        read_head(git_dir)


def test_invalid_packed_ref(tmp_path: Path, make_git_repo: GitRepoFactory) -> None:
    git_dir = make_git_repo(tmp_path, packed=True)
    (git_dir / "packed-refs").write_text("xyz refs/heads/next\n", encoding="utf-8")
    with pytest.raises(GitReadError):
        read_head(git_dir)


def test_unreadable_packed_refs(tmp_path: Path, make_git_repo: GitRepoFactory) -> None:
    git_dir = make_git_repo(tmp_path, packed=True)
    (git_dir / "packed-refs").write_bytes(b"\xff\xfe")
    with pytest.raises(GitReadError):
        read_head(git_dir)


def test_too_large_files_are_rejected(tmp_path: Path, make_git_repo: GitRepoFactory) -> None:
    git_dir = make_git_repo(tmp_path)
    (git_dir / "HEAD").write_text("x" * 5000, encoding="utf-8")
    with pytest.raises(GitReadError):
        read_head(git_dir)


def test_too_large_packed_refs(
    tmp_path: Path, make_git_repo: GitRepoFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    git_dir = make_git_repo(tmp_path, packed=True)
    monkeypatch.setattr("app.core.guide.git._MAX_PACKED_REFS_BYTES", 10)
    with pytest.raises(GitReadError):
        read_head(git_dir)


def test_missing_head(tmp_path: Path) -> None:
    (tmp_path / ".git").mkdir()
    with pytest.raises(GitReadError):
        read_head(tmp_path / ".git")
