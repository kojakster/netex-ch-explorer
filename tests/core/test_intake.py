"""Eigene Dateien annehmen: Namen, ZIP-Sicherheit, Grenzwerte, Arbeitsverzeichnis."""

from __future__ import annotations

import io
import stat
import zipfile
from pathlib import Path

import pytest

from app.core.config import ZipLimits
from app.core.dataset import FileNote
from app.core.intake import (
    MAX_NAME_LENGTH,
    Upload,
    Workspace,
    clean_name,
    receive,
)
from app.core.messages import MessageKey, Severity
from tests.support import FIXTURES_DIR

LIMITS = ZipLimits(
    max_total_bytes=10_000_000, max_file_bytes=2_000_000, max_files=20, max_compression_ratio=100
)
XML = (FIXTURES_DIR / "ch20_three_stops.xml").read_bytes()


def make_zip(entries: dict[str, bytes], *, symlinks: tuple[str, ...] = ()) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in entries.items():
            info = zipfile.ZipInfo(name)
            if name in symlinks:
                info.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(info, data, zipfile.ZIP_DEFLATED)
    return buffer.getvalue()


def keys(result_notes: list[FileNote]) -> list[MessageKey]:
    return [note.key for note in result_notes]


@pytest.fixture
def session(tmp_path: Path) -> Path:
    return Workspace(tmp_path / "work").new_session()


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("a.xml", "a.xml"),
        ("../../etc/passwd", "passwd"),
        ("C:\\Users\\x\\fahrplan.xml", "fahrplan.xml"),
        ("sub/dir/f.xml", "f.xml"),
        ("na<me>|?.xml", "na_me___.xml"),
        ("  .hidden. ", "hidden"),
        ("", "datei"),
        ("...", "datei"),
        ("CON.xml", "_CON.xml"),
        ("nul", "_nul"),
        ("CON .xml", "_CON .xml"),
        ("con ..xml", "_con ..xml"),
        ("COM¹", "_COM¹"),
        ("LPT².xml", "_LPT².xml"),
        ("com³.txt", "_com³.txt"),
        ("COM0.xml", "COM0.xml"),
        ("CONSOLE.xml", "CONSOLE.xml"),
        ("Zürich.xml", "Zürich.xml"),
        ("a\x00b.xml", "a_b.xml"),
    ],
)
def test_clean_name(raw: str, expected: str) -> None:
    assert clean_name(raw) == expected


def test_clean_name_is_limited() -> None:
    assert len(clean_name("a" * 1000 + ".xml")) <= MAX_NAME_LENGTH


def test_receives_xml_in_work_dir(session: Path) -> None:
    result = receive([Upload("a.xml", XML)], session, LIMITS)
    assert [source.name for source in result.sources] == ["a.xml"]
    assert result.sources[0].data == XML
    assert (session / "files" / "a.xml").read_bytes() == XML
    assert result.notes == []


def test_cleaned_name_is_reported(session: Path) -> None:
    result = receive([Upload("../x/a b?.xml", XML)], session, LIMITS)
    assert [source.name for source in result.sources] == ["a b_.xml"]
    [note] = result.notes
    assert note.key is MessageKey.FILE_NAME_CHANGED
    assert note.severity is Severity.INFO
    assert note.params == {"original": "../x/a b?.xml"}


def test_duplicate_names_are_made_unique(session: Path) -> None:
    result = receive([Upload("a.xml", XML), Upload("A.XML", XML)], session, LIMITS)
    assert [source.name for source in result.sources] == ["a.xml", "A_2.XML"]


def test_unique_rename_is_reported_at_the_final_name(session: Path) -> None:
    result = receive([Upload("a.xml", XML), Upload("A.XML", XML)], session, LIMITS)
    [note] = result.notes
    assert note.file_name == "A_2.XML"
    assert note.key is MessageKey.FILE_NAME_CHANGED
    assert note.params == {"original": "A.XML"}
    assert (session / "files" / "A_2.XML").read_bytes() == XML


def test_cleaned_name_taken_by_an_earlier_file_does_not_overwrite_it(session: Path) -> None:
    other = b"<other/>"
    result = receive([Upload("a_b.xml", XML), Upload("a?b.xml", other)], session, LIMITS)
    assert [source.name for source in result.sources] == ["a_b.xml", "a_b_2.xml"]
    assert [note.file_name for note in result.notes] == ["a_b_2.xml"]
    assert (session / "files" / "a_b.xml").read_bytes() == XML
    assert (session / "files" / "a_b_2.xml").read_bytes() == other
    assert [source.path for source in result.sources] == [
        session / "files" / "a_b.xml",
        session / "files" / "a_b_2.xml",
    ]


@pytest.mark.parametrize("name", ["a.txt", "a", "a.exe", "xml"])
def test_unsupported_types_are_rejected(session: Path, name: str) -> None:
    result = receive([Upload(name, b"x")], session, LIMITS)
    assert result.sources == []
    assert keys(result.notes) == [MessageKey.FILE_TYPE_UNSUPPORTED]


def test_empty_and_oversized_xml_are_rejected(session: Path) -> None:
    limits = ZipLimits(max_file_bytes=100)
    result = receive([Upload("e.xml", b""), Upload("g.xml", b"x" * 101)], session, limits)
    assert result.sources == []
    assert keys(result.notes) == [MessageKey.FILE_EMPTY, MessageKey.FILE_TOO_LARGE]
    assert result.notes[1].params == {"limit": 100}


def test_zip_with_xml_files(session: Path) -> None:
    archive = make_zip(
        {"NETWORK_OFFER.xml": XML, "sub/SITE_OFFER.xml": XML, "readme.txt": b"hallo"}
    )
    result = receive([Upload("lieferung.zip", archive)], session, LIMITS)
    assert [source.name for source in result.sources] == ["NETWORK_OFFER.xml", "sub/SITE_OFFER.xml"]
    assert (session / "zip1" / "entries" / "sub" / "SITE_OFFER.xml").read_bytes() == XML
    [note] = result.notes
    assert note.key is MessageKey.ZIP_ENTRIES_SKIPPED
    assert note.file_name == "lieferung.zip"
    assert note.params["count"] == 1
    assert note.params["examples"] == "readme.txt"


def test_zip_skips_os_noise(session: Path) -> None:
    archive = make_zip({"a.xml": XML, "__MACOSX/._a.xml": b"x", "sub/._b.xml": b"x"})
    result = receive([Upload("z.zip", archive)], session, LIMITS)
    assert [source.name for source in result.sources] == ["a.xml"]
    assert result.notes[0].params["count"] == 2


@pytest.mark.parametrize(
    "entry",
    ["../evil.xml", "a/../../evil.xml", "/etc/evil.xml", "\\evil.xml", "C:/evil.xml"],
)
def test_zip_slip_is_rejected(session: Path, tmp_path: Path, entry: str) -> None:
    archive = make_zip({entry: XML, "ok.xml": XML})
    result = receive([Upload("z.zip", archive)], session, LIMITS)
    assert [source.name for source in result.sources] == ["ok.xml"]
    assert keys(result.notes) == [MessageKey.ZIP_UNSAFE_PATH]
    assert not (tmp_path / "evil.xml").exists()
    assert not (tmp_path / "work" / "evil.xml").exists()


def test_zip_too_deep_is_rejected(session: Path) -> None:
    archive = make_zip({"/".join(["d"] * 20) + "/a.xml": XML})
    result = receive([Upload("z.zip", archive)], session, LIMITS)
    assert result.sources == []
    assert MessageKey.ZIP_UNSAFE_PATH in keys(result.notes)


def test_zip_symlink_is_rejected(session: Path) -> None:
    archive = make_zip({"link.xml": b"/etc/passwd", "ok.xml": XML}, symlinks=("link.xml",))
    result = receive([Upload("z.zip", archive)], session, LIMITS)
    assert [source.name for source in result.sources] == ["ok.xml"]
    assert keys(result.notes) == [MessageKey.ZIP_SYMLINK]
    assert not list(session.rglob("link.xml"))


def test_zip_with_too_many_entries(session: Path) -> None:
    limits = ZipLimits(max_files=3)
    archive = make_zip({f"f{n}.xml": XML for n in range(4)})
    result = receive([Upload("z.zip", archive)], session, limits)
    assert result.sources == []
    assert keys(result.notes) == [MessageKey.ZIP_TOO_MANY_FILES]
    assert result.notes[0].params == {"count": 4, "limit": 3}


def test_zip_total_size_declared(session: Path) -> None:
    limits = ZipLimits(max_total_bytes=len(XML) * 2 - 1)
    archive = make_zip({"a.xml": XML, "b.xml": XML})
    result = receive([Upload("z.zip", archive)], session, limits)
    assert result.sources == []
    assert keys(result.notes) == [MessageKey.ZIP_TOTAL_TOO_LARGE]


def test_zip_single_file_too_large(session: Path) -> None:
    limits = ZipLimits(max_file_bytes=len(XML) - 1)
    archive = make_zip({"a.xml": XML, "b.xml": XML[:100]})
    result = receive([Upload("z.zip", archive)], session, limits)
    assert [source.name for source in result.sources] == ["b.xml"]
    assert keys(result.notes) == [MessageKey.ZIP_ENTRY_TOO_LARGE]


def test_zip_compression_ratio(session: Path) -> None:
    bomb = b"<a>" + b"0" * 3_000_000 + b"</a>"
    limits = ZipLimits(max_file_bytes=10_000_000, max_compression_ratio=100)
    archive = make_zip({"bomb.xml": bomb, "ok.xml": XML})
    result = receive([Upload("z.zip", archive)], session, limits)
    assert [source.name for source in result.sources] == ["ok.xml"]
    [note] = result.notes
    assert note.key is MessageKey.ZIP_COMPRESSION_RATIO
    ratio = note.params["ratio"]
    assert isinstance(ratio, int)
    assert ratio > 100
    assert not (session / "zip1" / "entries" / "bomb.xml").exists()


class _Stream(io.BytesIO):
    """Ersatz für einen Eintrag, der mehr Bytes liefert, als der Kopf des Archivs angibt."""


def lying_archive(monkeypatch: pytest.MonkeyPatch, size: int) -> bytes:
    archive = make_zip({"a.xml": b"<a/>", "b.xml": b"<b/>"})
    monkeypatch.setattr(zipfile.ZipFile, "open", lambda *_args, **_kw: _Stream(b"x" * size))
    return archive


def test_zip_entry_larger_than_its_header_is_stopped(
    session: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = lying_archive(monkeypatch, 5000)
    result = receive([Upload("z.zip", archive)], session, ZipLimits(max_file_bytes=1000))
    assert result.sources == []
    assert keys(result.notes) == [MessageKey.ZIP_ENTRY_TOO_LARGE] * 2
    assert not list((session / "zip1" / "entries").rglob("*.xml"))


def test_zip_total_larger_than_its_headers_is_stopped(
    session: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    archive = lying_archive(monkeypatch, 600)
    limits = ZipLimits(max_total_bytes=1000, max_file_bytes=700)
    result = receive([Upload("z.zip", archive)], session, limits)
    assert result.sources == []
    assert keys(result.notes) == [MessageKey.ZIP_TOTAL_TOO_LARGE]


def test_total_limit_counts_all_files_of_an_upload(session: Path) -> None:
    limits = ZipLimits(max_total_bytes=100, max_file_bytes=100)
    uploads = [Upload("a.xml", b"x" * 60), Upload("b.xml", b"y" * 60), Upload("c.xml", b"z" * 40)]
    result = receive(uploads, session, limits)
    assert [source.name for source in result.sources] == ["a.xml", "c.xml"]
    [note] = result.notes
    assert (note.file_name, note.key) == ("b.xml", MessageKey.FILE_TOTAL_TOO_LARGE)
    assert note.params == {"limit": 100}
    assert not (session / "files" / "b.xml").exists()


def test_total_limit_counts_xml_and_zip_together(session: Path) -> None:
    limits = ZipLimits(max_total_bytes=100, max_file_bytes=100)
    archive = make_zip({"in.xml": b"x" * 60})
    result = receive([Upload("a.xml", b"y" * 60), Upload("z.zip", archive)], session, limits)
    assert [source.name for source in result.sources] == ["a.xml"]
    assert keys(result.notes) == [MessageKey.ZIP_TOTAL_TOO_LARGE]


def test_total_limit_counts_all_zips_of_an_upload(session: Path) -> None:
    limits = ZipLimits(max_total_bytes=100, max_file_bytes=100)
    first = make_zip({"a.xml": b"x" * 60})
    second = make_zip({"b.xml": b"y" * 60})
    result = receive([Upload("1.zip", first), Upload("2.zip", second)], session, limits)
    assert [source.name for source in result.sources] == ["a.xml"]
    assert [(n.file_name, n.key) for n in result.notes] == [
        ("2.zip", MessageKey.ZIP_TOTAL_TOO_LARGE)
    ]


def test_zip_that_is_not_a_zip(session: Path) -> None:
    result = receive([Upload("z.zip", b"das ist kein zip")], session, LIMITS)
    assert result.sources == []
    assert keys(result.notes) == [MessageKey.ZIP_UNREADABLE]


def test_zip_with_corrupt_entry(session: Path) -> None:
    archive = bytearray(make_zip({"a.xml": XML, "b.xml": XML}))
    position = archive.find(b"b.xml") + len(b"b.xml") + 30
    archive[position : position + 20] = b"\x00" * 20
    result = receive([Upload("z.zip", bytes(archive))], session, LIMITS)
    assert "a.xml" in [source.name for source in result.sources]
    assert MessageKey.ZIP_ENTRY_UNREADABLE in keys(result.notes)


def test_zip_without_xml(session: Path) -> None:
    result = receive([Upload("z.zip", make_zip({"a.txt": b"x"}))], session, LIMITS)
    assert result.sources == []
    assert keys(result.notes) == [MessageKey.ZIP_ENTRIES_SKIPPED, MessageKey.ZIP_NO_XML]


def test_zip_empty_xml_entry(session: Path) -> None:
    result = receive([Upload("z.zip", make_zip({"a.xml": b""}))], session, LIMITS)
    assert result.sources == []
    assert [(n.file_name, n.key) for n in result.notes] == [("a.xml", MessageKey.FILE_EMPTY)]


def test_zip_entry_names_are_cleaned_and_unique(session: Path) -> None:
    archive = make_zip({"a?b.xml": XML, "a_b.xml": XML})
    result = receive([Upload("z.zip", archive)], session, LIMITS)
    assert [source.name for source in result.sources] == ["a_b.xml", "a_b_2.xml"]
    assert [(n.file_name, n.params["original"]) for n in result.notes] == [
        ("a_b.xml", "a?b.xml"),
        ("a_b_2.xml", "a_b.xml"),
    ]


def test_two_zips_do_not_collide(session: Path) -> None:
    archive = make_zip({"a.xml": XML})
    result = receive([Upload("1.zip", archive), Upload("2.zip", archive)], session, LIMITS)
    assert [source.name for source in result.sources] == ["a.xml", "a_2.xml"]


class TestWorkspace:
    def test_session_lifecycle(self, tmp_path: Path) -> None:
        workspace = Workspace(tmp_path / "work")
        session = workspace.new_session()
        assert session.parent == tmp_path / "work"
        (session / "x.txt").write_text("x", encoding="utf-8")
        workspace.remove_session(session)
        assert not session.exists()

    def test_remove_session_ignores_foreign_paths(self, tmp_path: Path) -> None:
        workspace = Workspace(tmp_path / "work")
        workspace.new_session()
        foreign = tmp_path / "other"
        foreign.mkdir()
        workspace.remove_session(foreign)
        workspace.remove_session(tmp_path / "work" / "kurz")
        assert foreign.exists()

    def test_clear_removes_only_session_folders(self, tmp_path: Path) -> None:
        root = tmp_path / "work"
        workspace = Workspace(root)
        session = workspace.new_session()
        keep = root / "notizen"
        keep.mkdir()
        loose = root / ("a" * 20)
        loose.write_text("datei", encoding="utf-8")
        workspace.clear()
        assert not session.exists()
        assert not loose.exists()
        assert keep.exists()

    def test_clear_without_folder_and_with_symlink(self, tmp_path: Path) -> None:
        Workspace(tmp_path / "fehlt").clear()
        target = tmp_path / "ziel"
        victim = target / ("v" * 20)
        victim.mkdir(parents=True)
        link = tmp_path / "work"
        link.symlink_to(target, target_is_directory=True)
        Workspace(link).clear()
        assert victim.exists()

    def test_clear_does_not_follow_symlinks_inside(self, tmp_path: Path) -> None:
        root = tmp_path / "work"
        root.mkdir()
        outside = tmp_path / "ausserhalb"
        outside.mkdir()
        (outside / "wichtig.txt").write_text("x", encoding="utf-8")
        (root / ("l" * 20)).symlink_to(outside, target_is_directory=True)
        Workspace(root).clear()
        assert (outside / "wichtig.txt").exists()
