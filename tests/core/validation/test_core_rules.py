"""Schweizer Kernregeln: jede Regel der Liste wird aus ihren Daten verletzt und eingehalten."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.core.dataset import SourceFile, open_dataset
from app.core.diagnostics import DiagnosticCategory
from app.core.index.dataset_index import DatasetIndex
from app.core.messages import MessageKey, Severity
from app.core.validation.core_rules import (
    CORE_RULES,
    CoreRule,
    RuleFinding,
    RuleKind,
    check_core_rules,
)
from tests.support import FIXTURES_DIR, REF_TARGETS

NAMESPACE = "http://www.netex.org.uk/netex"
RULES_BY_ID = {rule.id: rule for rule in CORE_RULES}


def index_of(xml: str, name: str = "x.xml") -> DatasetIndex:
    dataset = open_dataset([SourceFile(name, xml.encode())], (), REF_TARGETS)
    return dataset.index


def check(xml: str) -> list[RuleFinding]:
    return check_core_rules(index_of(xml), frozenset({1}))


def ids(findings: list[RuleFinding]) -> list[str]:
    return [str(f.diagnostic.params.get("rule", "-")) for f in findings]


def nested(path: tuple[str, ...], leaf: str) -> str:
    """Verschachtelte Elemente für einen Pfad; das letzte trägt `leaf` (Text oder Attribute)."""
    *parents, last = path
    inner = f"<{last}{leaf}" if leaf.startswith(" ") else f"<{last}>{leaf}"
    inner += "/>" if leaf.startswith(" ") else f"</{last}>"
    for parent in reversed(parents):
        inner = f"<{parent}>{inner}</{parent}>"
    return inner


def document(context: str, children: str = "") -> str:
    return f'<R xmlns="{NAMESPACE}"><{context} id="c1" version="1">{children}</{context}></R>'


def value_leaf(rule: CoreRule, value: str) -> str:
    return f' {rule.attribute}="{value}"' if rule.attribute else value


def test_every_rule_names_an_existing_guide_chapter(guide_path: Path) -> None:
    for rule in CORE_RULES:
        assert guide_path.joinpath(*rule.chapter.split("/")).is_file(), rule.id
        assert guide_path.joinpath("src", "templates", rule.template).is_file(), rule.id


def test_diagnostics_name_the_chapter_of_the_rule() -> None:
    [finding] = [
        f for f in check(document("TimingLink")) if f.diagnostic.params["rule"] == "CH-TL-01"
    ]
    assert finding.diagnostic.params["chapter"] == "src/08_timetable.md"
    journey_part = check(
        document("JourneyPart", nested(("PurposeOfJourneyPartitionRef",), ' ref="x"'))
    )
    assert journey_part[0].diagnostic.params["chapter"] == "src/uc05_journey_parts.md"


def test_core_rule_list_is_complete_and_unique() -> None:
    assert len(RULES_BY_ID) == len(CORE_RULES) == 30
    assert "CH-SJP-08" not in RULES_BY_ID
    assert "CH-SJ-16" not in RULES_BY_ID


@pytest.mark.parametrize("rule", CORE_RULES, ids=lambda rule: rule.id)
def test_rule_source_and_severity(rule: CoreRule) -> None:
    assert rule.source.startswith("templates/")
    assert rule.template in rule.source
    expected = {
        RuleKind.EXPECTED: {Severity.INFO},
        RuleKind.REQUIRED: {Severity.ERROR},
        RuleKind.EXACTLY_ONE: {Severity.ERROR},
        RuleKind.FORBIDDEN: {Severity.ERROR},
        RuleKind.VALUE: {Severity.ERROR, Severity.INFO, Severity.WARNING},
    }
    assert rule.severity in expected[rule.kind]


@pytest.mark.parametrize(
    "rule",
    [
        r
        for r in CORE_RULES
        if r.kind in {RuleKind.REQUIRED, RuleKind.EXPECTED, RuleKind.EXACTLY_ONE}
    ],
    ids=lambda r: r.id,
)
def test_missing_element_violates(rule: CoreRule) -> None:
    findings = [
        f for f in check(document(rule.context)) if f.diagnostic.params.get("rule") == rule.id
    ]
    [finding] = findings
    diagnostic = finding.diagnostic
    assert diagnostic.category is DiagnosticCategory.PROFILE_RULE
    assert diagnostic.severity is rule.severity
    assert diagnostic.params["source"] == rule.source
    assert diagnostic.params["element"] == rule.context
    assert diagnostic.params["id"] == "c1"
    assert diagnostic.position is not None
    expected_key = {
        RuleKind.REQUIRED: MessageKey.CORE_REQUIRED_MISSING,
        RuleKind.EXPECTED: MessageKey.CORE_EXPECTED_MISSING,
        RuleKind.EXACTLY_ONE: MessageKey.CORE_EXACTLY_ONE,
    }[rule.kind]
    assert diagnostic.key is expected_key


@pytest.mark.parametrize(
    "rule",
    [
        r
        for r in CORE_RULES
        if r.kind in {RuleKind.REQUIRED, RuleKind.EXPECTED, RuleKind.EXACTLY_ONE}
    ],
    ids=lambda r: r.id,
)
def test_present_element_complies(rule: CoreRule) -> None:
    for path in rule.targets:  # bei Alternativen genügt jede
        children = nested(path, "")
        assert rule.id not in ids(check(document(rule.context, children)))


@pytest.mark.parametrize(
    "rule", [r for r in CORE_RULES if r.kind is RuleKind.EXACTLY_ONE], ids=lambda r: r.id
)
def test_two_elements_violate_exactly_one(rule: CoreRule) -> None:
    [path] = rule.targets
    findings = check(document(rule.context, nested(path, "") * 2))
    [finding] = [f for f in findings if f.diagnostic.params.get("rule") == rule.id]
    assert finding.diagnostic.params["found"] == 2


@pytest.mark.parametrize(
    "rule", [r for r in CORE_RULES if r.kind is RuleKind.FORBIDDEN], ids=lambda r: r.id
)
def test_forbidden_element_violates(rule: CoreRule) -> None:
    [path] = rule.targets
    children = nested(path, rule.text_equals or "")
    findings = [
        f
        for f in check(document(rule.context, children))
        if f.diagnostic.params.get("rule") == rule.id
    ]
    [finding] = findings
    assert finding.diagnostic.key is MessageKey.CORE_FORBIDDEN_PRESENT
    assert finding.diagnostic.params["source"] == rule.source


def test_forbidden_key_only_for_sjyid() -> None:
    rule = RULES_BY_ID["CH-SJ-14"]
    [path] = rule.targets
    assert rule.id not in ids(check(document("ServiceJourney", nested(path, "andere"))))
    assert rule.id in ids(check(document("ServiceJourney", nested(path, "sjyid "))))


@pytest.mark.parametrize(
    "rule", [r for r in CORE_RULES if r.kind is RuleKind.VALUE], ids=lambda r: r.id
)
def test_value_rule(rule: CoreRule) -> None:
    [path] = rule.targets
    bad = check(document(rule.context, nested(path, value_leaf(rule, "unzulaessig"))))
    [finding] = [f for f in bad if f.diagnostic.params.get("rule") == rule.id]
    assert finding.diagnostic.key is MessageKey.CORE_VALUE_NOT_ALLOWED
    assert finding.diagnostic.params["value"] == "unzulaessig"
    assert finding.diagnostic.params["allowed"] == ", ".join(rule.allowed)
    for allowed in rule.allowed:
        good = check(document(rule.context, nested(path, value_leaf(rule, allowed))))
        assert rule.id not in ids(good)
    assert rule.id not in ids(check(document(rule.context)))


def test_purpose_of_journey_partition_accepts_both_spellings() -> None:
    rule = RULES_BY_ID["CH-JP-01"]
    assert rule.severity is Severity.WARNING
    assert "ch:1:PurposeOfJouryneyPartition:TypeOfProductCategoryChange" in rule.allowed
    assert "ch:1:PurposeOfJourneyPartition:TypeOfProductCategoryChange" in rule.allowed
    assert "ch:1:PurposeOfJourneyPartition:FacilityChange" in rule.allowed


def test_value_rule_without_attribute_is_ignored() -> None:
    xml = document("JourneyPart", "<PurposeOfJourneyPartitionRef/>")
    assert "CH-JP-01" not in ids(check(xml))


def test_alternatives_in_wait_time() -> None:
    rule = RULES_BY_ID["CH-TDT-05"]
    assert rule.id in ids(check(document("JourneyWaitTime", "<WaitTime>PT1M</WaitTime>")))
    for alternative in ("ScheduledStopPointRef", "StopPointInJourneyPatternRef", "TimingPointRef"):
        xml = document("JourneyWaitTime", f"<{alternative} ref='a'/>")
        assert rule.id not in ids(check(xml))


def test_stub_journey_gets_a_note_instead_of_rules() -> None:
    xml = document(
        "ServiceJourney", "<privateCodes><PrivateCode type='sjyid'>1</PrivateCode></privateCodes>"
    )
    [finding] = check(xml)
    assert finding.diagnostic.key is MessageKey.CORE_STUB_JOURNEY
    assert finding.diagnostic.severity is Severity.INFO
    assert finding.diagnostic.params == {"element": "ServiceJourney", "id": "c1"}


def test_journey_with_more_than_private_codes_is_not_a_stub() -> None:
    xml = document("ServiceJourney", "<privateCodes/><DepartureTime>08:00:00</DepartureTime>")
    findings = check(xml)
    assert MessageKey.CORE_STUB_JOURNEY not in {f.diagnostic.key for f in findings}
    assert "CH-SJ-04" in ids(findings)


def test_journey_without_children_is_not_a_stub() -> None:
    findings = check(document("ServiceJourney"))
    assert MessageKey.CORE_STUB_JOURNEY not in {f.diagnostic.key for f in findings}
    assert "CH-SJ-04" in ids(findings)


def test_rules_only_apply_to_the_given_files() -> None:
    index = index_of(document("ServiceJourney"))
    assert check_core_rules(index, frozenset()) == []
    assert check_core_rules(index, frozenset({1}))


def test_findings_are_sorted_by_position() -> None:
    xml = (
        f'<R xmlns="{NAMESPACE}"><ServiceJourney id="a"/><TimingLink id="b"/>'
        '<ServiceJourney id="c"/></R>'
    )
    findings = check(xml)
    positions = [f.diagnostic.position.byte for f in findings if f.diagnostic.position]
    assert positions == sorted(positions)
    assert len(findings) > 5


def test_three_stops_fixture_has_no_violation() -> None:
    data = (FIXTURES_DIR / "ch20_three_stops.xml").read_bytes()
    index = open_dataset([SourceFile("t.xml", data)], (), REF_TARGETS).index
    assert check_core_rules(index, frozenset({1})) == []


def test_calls_fixture_violates_with_source() -> None:
    data = (FIXTURES_DIR / "ch20_calls.xml").read_bytes()
    index = open_dataset([SourceFile("c.xml", data)], (), REF_TARGETS).index
    findings = check_core_rules(index, frozenset({1}))
    [calls] = [f for f in findings if f.diagnostic.params.get("rule") == "CH-SJ-13"]
    assert calls.diagnostic.key is MessageKey.CORE_FORBIDDEN_PRESENT
    assert calls.diagnostic.params["source"] == "templates/ServiceJourney.xml Z. 145-153"
    assert calls.diagnostic.position is not None
    assert calls.diagnostic.position.line > 1
