from __future__ import annotations

from pathlib import Path

import pytest

from app.core.guide.examples import ExampleResult
from app.core.guide.guide_tested import ExampleRecord, GuideTestRecord, write_test_record
from app.core.guide.layout import MAPPING_TABLE_FILE, XSD_MAIN_FILE
from app.core.guide.mapping import SHEET_SPECS
from app.core.guide.status import ExampleChange, GuideTestState, inspect_guide, read_guide_revision
from app.core.messages import MessageKey, Severity
from tests.support import SHA_A, SHA_B


@pytest.fixture
def guide(synthetic_guide: Path) -> Path:
    return synthetic_guide


def keys(status_issues: tuple[object, ...]) -> list[object]:
    return [getattr(issue, "key", None) for issue in status_issues]


def test_tested_guide(guide: Path, tmp_path: Path) -> None:
    record = tmp_path / "guide-tested.json"
    write_test_record(record, GuideTestRecord(guide_commit=SHA_A, xsd_commit=SHA_B))
    status = inspect_guide(guide, record)
    assert status.found
    assert status.revision.branch == "next"
    assert status.revision.commit == SHA_A
    assert status.revision.xsd_commit == SHA_B
    assert status.xsd_present
    assert status.test_state is GuideTestState.TESTED
    assert status.tested_commit == SHA_A
    assert status.issues == ()
    assert set(status.mapping.sheets) == {spec.name for spec in SHEET_SPECS}


def test_differing_guide(guide: Path, tmp_path: Path) -> None:
    record = tmp_path / "guide-tested.json"
    write_test_record(record, GuideTestRecord(guide_commit=SHA_B, xsd_commit=SHA_B))
    status = inspect_guide(guide, record)
    assert status.test_state is GuideTestState.DIFFERS
    issue = status.issues[0]
    assert issue.key is MessageKey.GUIDE_TESTED_DIFFERS
    assert issue.params["testedCommit"] == SHA_B[:7]
    assert issue.params["testedXsdCommit"] == SHA_B[:7]


def test_differing_xsd_counts_as_differing(guide: Path, tmp_path: Path) -> None:
    record = tmp_path / "guide-tested.json"
    write_test_record(record, GuideTestRecord(guide_commit=SHA_A, xsd_commit=None))
    status = inspect_guide(guide, record)
    assert status.test_state is GuideTestState.DIFFERS
    assert status.issues[0].params["testedXsdCommit"] == "-"


def test_never_tested(guide: Path, tmp_path: Path) -> None:
    status = inspect_guide(guide, tmp_path / "fehlt.json")
    assert status.test_state is GuideTestState.NEVER_TESTED
    assert keys(status.issues) == [MessageKey.GUIDE_NEVER_TESTED]


def test_invalid_test_record(guide: Path, tmp_path: Path) -> None:
    record = tmp_path / "guide-tested.json"
    record.write_text("{", encoding="utf-8")
    status = inspect_guide(guide, record)
    assert status.test_state is GuideTestState.UNKNOWN
    assert keys(status.issues) == [MessageKey.GUIDE_TEST_RECORD_INVALID]


def test_missing_xsd(guide: Path, tmp_path: Path) -> None:
    guide.joinpath(*XSD_MAIN_FILE.parts).unlink()
    status = inspect_guide(guide, tmp_path / "fehlt.json")
    assert not status.xsd_present
    xsd_issue = next(i for i in status.issues if i.key is MessageKey.GUIDE_XSD_MISSING)
    assert xsd_issue.params["command"] == "git submodule update --init --depth 1"


def test_missing_mapping_table(guide: Path, tmp_path: Path) -> None:
    guide.joinpath(*MAPPING_TABLE_FILE.parts).unlink()
    status = inspect_guide(guide, tmp_path / "fehlt.json")
    assert MessageKey.MAPPING_FILE_MISSING in keys(status.issues)


def test_guide_not_found(tmp_path: Path) -> None:
    status = inspect_guide(tmp_path / "fehlt", tmp_path / "guide-tested.json")
    assert not status.found
    assert status.test_state is GuideTestState.UNKNOWN
    assert keys(status.issues) == [MessageKey.GUIDE_NOT_FOUND]


def test_guide_without_git(tmp_path: Path) -> None:
    (tmp_path / "guide").mkdir()
    record = tmp_path / "guide-tested.json"
    write_test_record(record, GuideTestRecord(guide_commit=SHA_A, xsd_commit=None))
    status = inspect_guide(tmp_path / "guide", record)
    assert status.revision.commit is None
    assert status.test_state is GuideTestState.UNKNOWN
    assert MessageKey.GUIDE_NOT_GIT in keys(status.issues)


def test_unreadable_git(guide: Path) -> None:
    (guide / ".git" / "HEAD").write_text("kaputt", encoding="utf-8")
    revision = read_guide_revision(guide)
    assert revision.commit is None
    assert keys(revision.issues) == [MessageKey.GUIDE_GIT_UNREADABLE]


def test_missing_xsd_submodule_is_no_git_issue(guide: Path) -> None:
    (guide / "xsd" / ".git").unlink()
    revision = read_guide_revision(guide)
    assert revision.xsd_commit is None
    assert revision.issues == ()


def test_examples_are_analyzed(guide: Path, tmp_path: Path) -> None:
    record = tmp_path / "guide-tested.json"
    status = inspect_guide(guide, record)
    by_name = {example.name: example for example in status.examples}
    assert list(by_name) == ["broken_xml.xml", "ch20_midnight.xml", "ch20_three_stops.xml"]
    assert by_name["ch20_three_stops.xml"].title == "Synthetische Fahrt"
    assert by_name["broken_xml.xml"].title == "Kaputt"
    assert by_name["ch20_midnight.xml"].title is None
    assert by_name["broken_xml.xml"].result is ExampleResult.UNREADABLE
    assert by_name["broken_xml.xml"].counts == {Severity.ERROR: 1}
    assert by_name["ch20_three_stops.xml"].result is ExampleResult.CLEAN
    assert {example.change for example in status.examples} == {ExampleChange.UNTESTED}


def test_example_changes_against_record(guide: Path, tmp_path: Path) -> None:
    record = tmp_path / "guide-tested.json"
    first = {example.name: example for example in inspect_guide(guide, record).examples}
    three = first["ch20_three_stops.xml"]
    assert three.sha256 is not None
    write_test_record(
        record,
        GuideTestRecord(
            SHA_A,
            SHA_B,
            {
                "ch20_three_stops.xml": ExampleRecord(three.sha256, ExampleResult.CLEAN),
                "ch20_midnight.xml": ExampleRecord("0" * 64, ExampleResult.CLEAN),
            },
        ),
    )
    changes = {example.name: example.change for example in inspect_guide(guide, record).examples}
    assert changes == {
        "ch20_three_stops.xml": ExampleChange.UNCHANGED,
        "ch20_midnight.xml": ExampleChange.CHANGED,
        "broken_xml.xml": ExampleChange.NEW,
    }


def test_example_status_uses_the_reference_target_list(guide: Path, tmp_path: Path) -> None:
    role_file = guide / "src" / "examples" / "zz_role.xml"
    role_file.write_text(
        "<R><Operator id='o1' version='1'/><ResponsibleOrganisationRef ref='o1' version='1'/></R>",
        encoding="utf-8",
    )
    record = tmp_path / "guide-tested.json"

    def result(targets: dict[str, tuple[str, ...]] | None) -> ExampleResult:
        examples = inspect_guide(guide, record, targets).examples
        return {example.name: example.result for example in examples}["zz_role.xml"]

    assert result(None) is ExampleResult.NOTES
    assert result({"ResponsibleOrganisationRef": ("Operator",)}) is ExampleResult.CLEAN
