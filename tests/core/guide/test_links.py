"""Verweise auf Guide-Kapitel über `src/A5_annex_index.md` im exakt verwendeten Commit."""

from __future__ import annotations

from pathlib import Path

from app.core.guide.layout import ANNEX_INDEX_FILE, GUIDE_REPOSITORY_URL
from app.core.guide.links import GuideLinks, guide_url, read_guide_links
from tests.support import SHA_A

INDEX = "\n".join(
    [
        "# Index",
        "",
        "- ServiceJourney: [SJ](site/tables/SJ.html), [02_files](02_files.html), [t](08_t.html)",
        "- Quay: [Quay](site/tables/Quay.html), [A3_annex](A3_annex.html), [u](uc04_u.html#x)",
        "- Nur Tabelle: [T](site/tables/T.html), [index](index.html)",
        "- Zeile ohne Muster",
    ]
)


def write_index(guide: Path, text: str = INDEX) -> None:
    path = guide.joinpath(*ANNEX_INDEX_FILE.parts)
    path.parent.mkdir(parents=True)
    path.write_text(text, encoding="utf-8")


def test_first_chapter_of_the_index_is_used(tmp_path: Path) -> None:
    write_index(tmp_path)
    links = read_guide_links(tmp_path)
    assert links.chapter("ServiceJourney") == "src/02_files.md"
    assert links.chapter("Quay") == "src/uc04_u.md"


def test_unknown_or_chapterless_elements_have_no_link(tmp_path: Path) -> None:
    write_index(tmp_path)
    links = read_guide_links(tmp_path)
    assert links.chapter("Unbekannt") is None
    assert links.chapter("Nur") is None
    assert links.chapter(None) is None


def test_missing_or_oversized_index_gives_no_links(tmp_path: Path) -> None:
    assert read_guide_links(tmp_path) == GuideLinks()
    write_index(tmp_path, "- A: [x](01_a.html)\n" + "x" * 2_100_000)
    assert read_guide_links(tmp_path) == GuideLinks()


def test_unreadable_index_gives_no_links(tmp_path: Path) -> None:
    path = tmp_path.joinpath(*ANNEX_INDEX_FILE.parts)
    path.mkdir(parents=True)
    assert read_guide_links(tmp_path) == GuideLinks()


def test_url_names_the_exact_commit() -> None:
    assert (
        guide_url(SHA_A, "src/08_timetable.md")
        == f"{GUIDE_REPOSITORY_URL}/blob/{SHA_A}/src/08_timetable.md"
    )


def test_url_needs_a_valid_commit_and_path() -> None:
    assert guide_url(None, "src/a.md") is None
    assert guide_url("main", "src/a.md") is None
    assert guide_url(SHA_A, None) is None


def test_real_index_links_service_journey(guide_path: Path) -> None:
    links = read_guide_links(guide_path)
    chapter = links.chapter("ServiceJourney")
    assert chapter is not None
    assert guide_path.joinpath(*chapter.split("/")).is_file()
