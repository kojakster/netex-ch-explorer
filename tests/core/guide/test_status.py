from __future__ import annotations

import sqlite3
from pathlib import Path

import pytest
from lxml.etree import LxmlError

from app.core.dataset import Dataset
from app.core.guide.examples import ExampleResult
from app.core.guide.guide_tested import ExampleRecord, GuideTestRecord, write_test_record
from app.core.guide.layout import MAPPING_TABLE_FILE, XSD_MAIN_FILE
from app.core.guide.mapping import SHEET_SPECS
from app.core.guide.status import (
    ExampleChange,
    GuideStatus,
    GuideTestState,
    complete_examples,
    fail_pending_examples,
    inspect_guide,
    read_guide_revision,
)
from app.core.messages import MessageKey, Severity
from app.core.validation.engine import ValidationEngine
from app.core.validation.result import ValidationSummary
from tests.support import EXPECTED_DATE, REF_TARGETS, SHA_A, SHA_B, write_loose


@pytest.fixture
def guide(synthetic_guide: Path) -> Path:
    return synthetic_guide


def keys(status_issues: tuple[object, ...]) -> list[object]:
    return [getattr(issue, "key", None) for issue in status_issues]


def test_tested_guide(guide: Path, tmp_path: Path) -> None:
    record = tmp_path / "guide-tested.json"
    write_test_record(record, GuideTestRecord(guide_commit=SHA_A, xsd_commit=SHA_B))
    status = inspect_guide(guide, record, REF_TARGETS)
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
    status = inspect_guide(guide, record, REF_TARGETS)
    assert status.test_state is GuideTestState.DIFFERS
    issue = status.issues[0]
    assert issue.key is MessageKey.GUIDE_TESTED_DIFFERS
    assert issue.params["testedCommit"] == SHA_B[:7]
    assert issue.params["testedXsdCommit"] == SHA_B[:7]


def test_differing_xsd_counts_as_differing(guide: Path, tmp_path: Path) -> None:
    record = tmp_path / "guide-tested.json"
    write_test_record(record, GuideTestRecord(guide_commit=SHA_A, xsd_commit=None))
    status = inspect_guide(guide, record, REF_TARGETS)
    assert status.test_state is GuideTestState.DIFFERS
    assert status.issues[0].params["testedXsdCommit"] == "-"


def test_never_tested(guide: Path, tmp_path: Path) -> None:
    status = inspect_guide(guide, tmp_path / "fehlt.json", REF_TARGETS)
    assert status.test_state is GuideTestState.NEVER_TESTED
    assert keys(status.issues) == [MessageKey.GUIDE_NEVER_TESTED]


def test_invalid_test_record(guide: Path, tmp_path: Path) -> None:
    record = tmp_path / "guide-tested.json"
    record.write_text("{", encoding="utf-8")
    status = inspect_guide(guide, record, REF_TARGETS)
    assert status.test_state is GuideTestState.UNKNOWN
    assert keys(status.issues) == [MessageKey.GUIDE_TEST_RECORD_INVALID]


def test_missing_xsd(guide: Path, tmp_path: Path) -> None:
    guide.joinpath(*XSD_MAIN_FILE.parts).unlink()
    status = inspect_guide(guide, tmp_path / "fehlt.json", REF_TARGETS)
    assert not status.xsd_present
    xsd_issue = next(i for i in status.issues if i.key is MessageKey.GUIDE_XSD_MISSING)
    assert xsd_issue.params["command"] == "git submodule update --init --depth 1"


def test_missing_mapping_table(guide: Path, tmp_path: Path) -> None:
    guide.joinpath(*MAPPING_TABLE_FILE.parts).unlink()
    status = inspect_guide(guide, tmp_path / "fehlt.json", REF_TARGETS)
    assert MessageKey.MAPPING_FILE_MISSING in keys(status.issues)


def test_guide_not_found(tmp_path: Path) -> None:
    status = inspect_guide(tmp_path / "fehlt", tmp_path / "guide-tested.json", REF_TARGETS)
    assert not status.found
    assert status.test_state is GuideTestState.UNKNOWN
    assert keys(status.issues) == [MessageKey.GUIDE_NOT_FOUND]


def test_guide_without_git(tmp_path: Path) -> None:
    (tmp_path / "guide").mkdir()
    record = tmp_path / "guide-tested.json"
    write_test_record(record, GuideTestRecord(guide_commit=SHA_A, xsd_commit=None))
    status = inspect_guide(tmp_path / "guide", record, REF_TARGETS)
    assert status.revision.commit is None
    assert status.test_state is GuideTestState.UNKNOWN
    assert MessageKey.GUIDE_NOT_GIT in keys(status.issues)


def test_revision_has_the_commit_date_when_the_object_is_readable(guide: Path) -> None:
    assert read_guide_revision(guide).commit_date is None  # SHA_A gibt es als Objekt nicht
    sha = write_loose(guide / ".git")
    (guide / ".git" / "refs" / "heads" / "next").write_text(f"{sha}\n", encoding="utf-8")
    revision = read_guide_revision(guide)
    assert revision.commit == sha
    assert revision.commit_date == EXPECTED_DATE


def test_revision_without_commit_has_no_date(guide: Path) -> None:
    (guide / ".git" / "refs" / "heads" / "next").unlink()
    assert read_guide_revision(guide).commit_date is None


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
    status = inspect_guide(guide, record, REF_TARGETS)
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
    first = {
        example.name: example for example in inspect_guide(guide, record, REF_TARGETS).examples
    }
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
    changes = {
        example.name: example.change
        for example in inspect_guide(guide, record, REF_TARGETS).examples
    }
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

    def result(targets: dict[str, tuple[str, ...]]) -> ExampleResult | None:
        examples = inspect_guide(guide, record, targets).examples
        return {example.name: example.result for example in examples}["zz_role.xml"]

    # Bewusst ohne Liste: Der Name ohne `Ref` (`ResponsibleOrganisation`) trifft kein Objekt.
    assert result({}) is ExampleResult.NOTES
    assert result({"ResponsibleOrganisationRef": ("Operator",)}) is ExampleResult.CLEAN
    assert result(REF_TARGETS) is ExampleResult.CLEAN


def results(status: GuideStatus) -> dict[str, ExampleResult | None]:
    return {example.name: example.result for example in status.examples}


def test_validation_counts_in_the_example_status(guide: Path, tmp_path: Path) -> None:
    """Mit Prüfmaschine zählen die Kernregeln: `ch20_midnight.xml` hat keine Produktkategorie."""
    record = tmp_path / "guide-tested.json"
    plain = inspect_guide(guide, record, REF_TARGETS)
    assert results(plain)["ch20_midnight.xml"] is ExampleResult.CLEAN
    engine = ValidationEngine(guide, SHA_A)
    checked = inspect_guide(guide, record, REF_TARGETS, engine)
    assert results(checked)["ch20_midnight.xml"] is ExampleResult.ERRORS
    assert results(checked)["ch20_three_stops.xml"] is ExampleResult.CLEAN
    by_name = {example.name: example for example in checked.examples}
    assert by_name["ch20_midnight.xml"].counts == {Severity.ERROR: 2}


def test_deferred_examples_have_no_result_until_completed(guide: Path, tmp_path: Path) -> None:
    record = tmp_path / "guide-tested.json"
    engine = ValidationEngine(guide, SHA_A)
    pending = inspect_guide(guide, record, REF_TARGETS, engine, defer_examples=True)
    assert not pending.examples_ready
    assert [e.name for e in pending.examples] == [
        "broken_xml.xml",
        "ch20_midnight.xml",
        "ch20_three_stops.xml",
    ]
    assert set(results(pending).values()) == {None}
    assert pending.examples[2].title == "Synthetische Fahrt"
    done = complete_examples(pending, record, REF_TARGETS, engine)
    assert done.examples_ready
    assert results(done)["broken_xml.xml"] is ExampleResult.UNREADABLE
    assert results(done)["ch20_midnight.xml"] is ExampleResult.ERRORS
    assert complete_examples(done, record, REF_TARGETS, engine) is done


def test_completing_with_an_invalid_record_still_works(guide: Path, tmp_path: Path) -> None:
    record = tmp_path / "guide-tested.json"
    record.write_text("kein json", encoding="utf-8")
    engine = ValidationEngine(guide, SHA_A)
    pending = inspect_guide(guide, record, REF_TARGETS, engine, defer_examples=True)
    done = complete_examples(pending, record, REF_TARGETS, engine)
    assert done.examples_ready
    assert {example.change for example in done.examples} == {ExampleChange.UNTESTED}


def test_completing_a_missing_guide_changes_nothing(tmp_path: Path) -> None:
    engine = ValidationEngine(tmp_path / "fehlt", None)
    missing = inspect_guide(tmp_path / "fehlt", tmp_path / "t.json", REF_TARGETS, engine)
    assert complete_examples(missing, tmp_path / "t.json", REF_TARGETS, engine) is missing


def test_failing_example_does_not_stop_the_others(
    guide: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, caplog: pytest.LogCaptureFixture
) -> None:
    record = tmp_path / "guide-tested.json"
    engine = ValidationEngine(guide, SHA_A)
    original = engine.validate

    def validate(dataset: Dataset) -> ValidationSummary:
        if dataset.index.files()[0].name == "ch20_midnight.xml":
            raise LxmlError("kaputt")
        return original(dataset)

    monkeypatch.setattr(engine, "validate", validate)
    status = inspect_guide(guide, record, REF_TARGETS, engine)
    assert results(status) == {
        "broken_xml.xml": ExampleResult.UNREADABLE,
        "ch20_midnight.xml": ExampleResult.CHECK_FAILED,
        "ch20_three_stops.xml": ExampleResult.CLEAN,
    }
    failed = {example.name: example for example in status.examples}["ch20_midnight.xml"]
    assert failed.sha256 is not None
    assert failed.counts == {}
    assert "ch20_midnight.xml" in caplog.text


@pytest.mark.parametrize("error", [LxmlError("x"), sqlite3.OperationalError("x"), OSError("x")])
def test_targeted_errors_become_check_failed(
    guide: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch, error: Exception
) -> None:
    engine = ValidationEngine(guide, SHA_A)

    def explode(_dataset: Dataset) -> ValidationSummary:
        raise error

    monkeypatch.setattr(engine, "validate", explode)
    status = inspect_guide(guide, tmp_path / "t.json", REF_TARGETS, engine)
    assert results(status)["ch20_three_stops.xml"] is ExampleResult.CHECK_FAILED


def test_program_errors_are_not_swallowed(
    guide: Path, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    engine = ValidationEngine(guide, SHA_A)

    def explode(_dataset: Dataset) -> ValidationSummary:
        raise ValueError("Programmfehler")

    monkeypatch.setattr(engine, "validate", explode)
    with pytest.raises(ValueError, match="Programmfehler"):
        inspect_guide(guide, tmp_path / "t.json", REF_TARGETS, engine)


def test_fail_pending_examples_finishes_the_check(guide: Path, tmp_path: Path) -> None:
    record = tmp_path / "guide-tested.json"
    pending = inspect_guide(guide, record, REF_TARGETS, defer_examples=True)
    finished = fail_pending_examples(pending)
    assert finished.examples_ready
    assert set(results(finished).values()) == {ExampleResult.CHECK_FAILED}
