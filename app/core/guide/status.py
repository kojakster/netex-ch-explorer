"""Guide-Status für die Guide-Status-Box: Stand, XSD, Testnachweis und Mappingtabelle."""

from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass, field
from enum import StrEnum
from pathlib import Path
from typing import Final

from app.core.dataset import SourceFile, open_dataset
from app.core.guide.examples import ExampleResult, example_result, list_examples, read_example
from app.core.guide.git import GitHead, GitReadError, find_git_dir, read_head
from app.core.guide.guide_tested import (
    TEST_COMMAND,
    GuideTestRecord,
    GuideTestRecordError,
    read_test_record,
)
from app.core.guide.layout import (
    MAPPING_TABLE_FILE,
    XSD_FETCH_COMMAND,
    XSD_MAIN_FILE,
    XSD_SUBMODULE_DIR,
)
from app.core.guide.mapping import MappingTable, read_mapping_table
from app.core.messages import Issue, MessageKey, Severity

SHORT_COMMIT_LENGTH: Final = 7


class GuideTestState(StrEnum):
    """Verhältnis des vorhandenen Guide-Stands zum zuletzt erfolgreich getesteten."""

    TESTED = "tested"
    DIFFERS = "differs"
    NEVER_TESTED = "never_tested"
    UNKNOWN = "unknown"


class ExampleChange(StrEnum):
    """Stand eines Beispiels gegenüber dem letzten erfolgreichen Testlauf."""

    UNCHANGED = "unchanged"
    CHANGED = "changed"
    NEW = "new"
    UNTESTED = "untested"
    """Es gibt keinen gültigen Testnachweis."""


@dataclass(frozen=True)
class ExampleStatus:
    """Ein Beispiel mit Ergebnis beim Laden und Stand gegenüber dem Testnachweis."""

    name: str
    title: str | None
    sha256: str | None
    result: ExampleResult
    counts: dict[Severity, int]
    change: ExampleChange


@dataclass(frozen=True)
class GuideRevision:
    """Branch und Commits des Guide-Klons und seines XSD-Submoduls."""

    branch: str | None = None
    commit: str | None = None
    xsd_commit: str | None = None
    issues: tuple[Issue, ...] = ()


@dataclass(frozen=True)
class GuideStatus:
    """Alles, was die Guide-Status-Box anzeigt."""

    path: Path
    found: bool
    revision: GuideRevision
    xsd_present: bool
    test_state: GuideTestState
    tested_commit: str | None
    mapping: MappingTable
    examples: tuple[ExampleStatus, ...] = ()
    issues: tuple[Issue, ...] = field(default=())


def read_guide_revision(guide_path: Path) -> GuideRevision:
    """Liest Branch und Commit des Guides und den Commit des XSD-Submoduls."""
    issues: list[Issue] = []
    head = _read_git_head(guide_path, issues, missing_is_issue=True)
    xsd_dir = guide_path.joinpath(*XSD_SUBMODULE_DIR.parts)
    xsd_head = _read_git_head(xsd_dir, issues, missing_is_issue=False)
    return GuideRevision(
        branch=head.branch if head else None,
        commit=head.commit if head else None,
        xsd_commit=xsd_head.commit if xsd_head else None,
        issues=tuple(issues),
    )


def inspect_guide(
    guide_path: Path,
    test_record_path: Path,
    ref_targets: Mapping[str, tuple[str, ...]],
) -> GuideStatus:
    """Untersucht den Guide-Klon und vergleicht ihn mit dem Testnachweis.

    `ref_targets` (config/ref-targets.json) bestimmt, wie Referenzen der Beispiele aufgelöst werden.

    Bricht nie ab: Jedes Problem wird zu einer Meldung.
    """
    if not guide_path.is_dir():
        return GuideStatus(
            path=guide_path,
            found=False,
            revision=GuideRevision(),
            xsd_present=False,
            test_state=GuideTestState.UNKNOWN,
            tested_commit=None,
            mapping=MappingTable(),
            issues=(Issue(Severity.ERROR, MessageKey.GUIDE_NOT_FOUND, {"path": str(guide_path)}),),
        )
    revision = read_guide_revision(guide_path)
    issues = list(revision.issues)
    xsd_present = guide_path.joinpath(*XSD_MAIN_FILE.parts).is_file()
    if not xsd_present:
        issues.append(
            Issue(
                Severity.ERROR,
                MessageKey.GUIDE_XSD_MISSING,
                {"file": str(XSD_MAIN_FILE), "command": XSD_FETCH_COMMAND},
            )
        )
    record, record_valid = _read_record(test_record_path, issues)
    test_state, tested_commit = _compare_with_test_record(revision, record, record_valid, issues)
    mapping = read_mapping_table(guide_path.joinpath(*MAPPING_TABLE_FILE.parts))
    issues.extend(mapping.issues)
    return GuideStatus(
        path=guide_path,
        found=True,
        revision=revision,
        xsd_present=xsd_present,
        test_state=test_state,
        tested_commit=tested_commit,
        mapping=mapping,
        examples=tuple(analyze_examples(guide_path, record if record_valid else None, ref_targets)),
        issues=tuple(issues),
    )


def _read_git_head(
    work_tree: Path, issues: list[Issue], *, missing_is_issue: bool
) -> GitHead | None:
    try:
        git_dir = find_git_dir(work_tree)
        if git_dir is None:
            if missing_is_issue:
                issues.append(
                    Issue(Severity.WARNING, MessageKey.GUIDE_NOT_GIT, {"path": str(work_tree)})
                )
            return None
        return read_head(git_dir)
    except GitReadError:
        issues.append(
            Issue(Severity.WARNING, MessageKey.GUIDE_GIT_UNREADABLE, {"path": str(work_tree)})
        )
        return None


def _read_record(record_path: Path, issues: list[Issue]) -> tuple[GuideTestRecord | None, bool]:
    """Liest den Testnachweis; der zweite Wert ist `False`, wenn er ungültig ist."""
    try:
        return read_test_record(record_path), True
    except GuideTestRecordError:
        issues.append(
            Issue(
                Severity.WARNING, MessageKey.GUIDE_TEST_RECORD_INVALID, {"file": record_path.name}
            )
        )
        return None, False


def _compare_with_test_record(
    revision: GuideRevision,
    record: GuideTestRecord | None,
    record_valid: bool,
    issues: list[Issue],
) -> tuple[GuideTestState, str | None]:
    if not record_valid:
        return GuideTestState.UNKNOWN, None
    if record is None:
        issues.append(
            Issue(Severity.INFO, MessageKey.GUIDE_NEVER_TESTED, {"command": TEST_COMMAND})
        )
        return GuideTestState.NEVER_TESTED, None
    if revision.commit is None:
        return GuideTestState.UNKNOWN, record.guide_commit
    if record.guide_commit == revision.commit and record.xsd_commit == revision.xsd_commit:
        return GuideTestState.TESTED, record.guide_commit
    issues.append(
        Issue(
            Severity.INFO,
            MessageKey.GUIDE_TESTED_DIFFERS,
            {
                "testedCommit": _short(record.guide_commit),
                "testedXsdCommit": _short(record.xsd_commit),
                "command": TEST_COMMAND,
            },
        )
    )
    return GuideTestState.DIFFERS, record.guide_commit


def analyze_examples(
    guide_path: Path,
    record: GuideTestRecord | None,
    ref_targets: Mapping[str, tuple[str, ...]],
) -> list[ExampleStatus]:
    """Lädt jedes Beispiel einzeln und vergleicht es mit dem Testnachweis.

    Ein fehlerhaftes Beispiel beeinträchtigt die anderen nicht.
    """
    examples = list_examples(guide_path)
    statuses = []
    for example in examples:
        data = read_example(guide_path, example.name, examples)
        if data is None:
            statuses.append(
                ExampleStatus(
                    example.name,
                    example.title,
                    None,
                    ExampleResult.UNREADABLE,
                    {},
                    _change(record, example.name, None),
                )
            )
            continue
        dataset = open_dataset([SourceFile(example.name, data)], (), ref_targets)
        try:
            sha256 = dataset.index.files()[0].sha256
            counts: dict[Severity, int] = {}
            for item in dataset.index.diagnostics():
                counts[item.diagnostic.severity] = counts.get(item.diagnostic.severity, 0) + 1
            result = example_result(dataset)
        finally:
            dataset.close()
        statuses.append(
            ExampleStatus(
                example.name,
                example.title,
                sha256,
                result,
                counts,
                _change(record, example.name, sha256),
            )
        )
    return statuses


def _change(record: GuideTestRecord | None, name: str, sha256: str | None) -> ExampleChange:
    if record is None:
        return ExampleChange.UNTESTED
    tested = record.examples.get(name)
    if tested is None:
        return ExampleChange.NEW
    return ExampleChange.UNCHANGED if tested.sha256 == sha256 else ExampleChange.CHANGED


def _short(commit: str | None) -> str:
    """Kurzform einer Commit-ID für Meldungen; `-` wenn unbekannt."""
    return commit[:SHORT_COMMIT_LENGTH] if commit else "-"
