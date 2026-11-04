"""Validierung eines Datensatzes: Ablauf, Auslassungen und Ergebnisse am echten Guide-Stand."""

from __future__ import annotations

from collections import Counter
from collections.abc import Sequence
from pathlib import Path

import pytest

from app.core.dataset import Dataset, SourceFile, open_dataset
from app.core.diagnostics import Diagnostic, DiagnosticCategory
from app.core.guide.examples import examples_dir
from app.core.guide.layout import GENERAL_RULES_FILE, XSD_MAIN_FILE
from app.core.messages import MessageKey, Severity
from app.core.validation import engine as engine_module
from app.core.validation.engine import ValidationEngine
from app.core.validation.lxml_checks import NotCheckableError, ParsedDocument
from tests.support import FIXTURES_DIR, REF_TARGETS

COMMIT = "a" * 40
NAMESPACE = "http://www.netex.org.uk/netex"
LAX_XSD = f"""<xs:schema xmlns:xs="http://www.w3.org/2001/XMLSchema" targetNamespace="{NAMESPACE}"
    xmlns="{NAMESPACE}" elementFormDefault="qualified">
  <xs:element name="PublicationDelivery">
    <xs:complexType>
      <xs:sequence>
        <xs:any processContents="skip" minOccurs="0" maxOccurs="unbounded"/>
      </xs:sequence>
      <xs:anyAttribute processContents="skip"/>
    </xs:complexType>
  </xs:element>
</xs:schema>"""
ORDER_RULE = """<schema xmlns="http://purl.oclc.org/dsdl/schematron">
  <pattern id="no_order_attribute"><rule context="*[@order]">
    <assert test="false()">order <value-of select="name()"/></assert></rule></pattern>
  <pattern id="neu"><rule context="*[@neu]"><assert test="false()">neu</assert></rule></pattern>
</schema>"""
PATTERN_BODY = "<ServiceJourneyPattern id='p'/><TimeDemandType id='t'/>"


def make_guide(root: Path, *, xsd: bool = True, rules: bool = True) -> Path:
    if xsd:
        path = root.joinpath(*XSD_MAIN_FILE.parts)
        path.parent.mkdir(parents=True)
        path.write_text(LAX_XSD, encoding="utf-8")
    if rules:
        path = root.joinpath(*GENERAL_RULES_FILE.parts)
        path.parent.mkdir(parents=True)
        path.write_text(ORDER_RULE, encoding="utf-8")
    return root


def dataset_of(*files: tuple[str, bytes]) -> Dataset:
    return open_dataset([SourceFile(name, data) for name, data in files], (), REF_TARGETS)


def ch20(body: str = "", root: str = "PublicationDelivery", attributes: str = "") -> bytes:
    return (
        f'<{root} xmlns="{NAMESPACE}" version="2.1" {attributes}>{PATTERN_BODY}{body}</{root}>'
    ).encode()


def counts(dataset: Dataset) -> Counter[tuple[str, str]]:
    return Counter((d.diagnostic.category, d.diagnostic.key) for d in dataset.index.diagnostics())


@pytest.fixture
def engine(tmp_path: Path) -> ValidationEngine:
    return ValidationEngine(make_guide(tmp_path / "guide"), COMMIT)


def test_validates_a_ch20_file(engine: ValidationEngine) -> None:
    dataset = dataset_of(("a.xml", ch20()))
    summary = engine.validate(dataset)
    assert dataset.validation is summary
    assert summary.guide_commit == COMMIT
    assert [(s.step_id, s.performed) for s in summary.steps] == [
        ("xsd", True),
        ("general_rules", True),
        ("ch_core_rules", True),
    ]
    assert [(f.file_id, f.checked) for f in summary.files] == [(1, True)]
    assert engine.xsd_loaded


def test_steps_are_not_performed_when_no_file_was_checkable(engine: ValidationEngine) -> None:
    data = (FIXTURES_DIR / "netex110_like.xml").read_bytes()
    summary = engine.validate(dataset_of(("netex110_like.xml", data)))
    assert [(s.step_id, s.performed) for s in summary.steps] == [
        ("xsd", False),
        ("general_rules", False),
        ("ch_core_rules", False),
    ]
    for step in summary.steps:
        assert step.reason is not None
        assert step.reason.key is MessageKey.VALIDATION_STEP_NO_FILE
        assert step.reason.params == {"step": step.step_id}


def test_empty_dataset_performs_no_step(engine: ValidationEngine) -> None:
    summary = engine.validate(dataset_of())
    assert not any(step.performed for step in summary.steps)


def test_lxml_steps_are_not_performed_when_the_only_file_is_uncheckable(
    engine: ValidationEngine, monkeypatch: pytest.MonkeyPatch
) -> None:
    def reject(_data: bytes) -> ParsedDocument:
        raise NotCheckableError("Grund")

    monkeypatch.setattr(engine_module, "parse_safely", reject)
    summary = engine.validate(dataset_of(("a.xml", ch20())))
    assert {s.step_id: s.performed for s in summary.steps} == {
        "xsd": False,
        "general_rules": False,
        "ch_core_rules": True,
    }


def test_findings_of_a_file_are_added_with_one_call(
    engine: ValidationEngine, monkeypatch: pytest.MonkeyPatch
) -> None:
    dataset = dataset_of(("a.xml", ch20("<A order='1'/><B order='2'/>")), ("b.xml", ch20()))
    calls: list[int] = []
    original = dataset.index.add_diagnostics

    def spy(file_id: int, diagnostics: Sequence[Diagnostic]) -> None:
        calls.append(file_id)
        original(file_id, diagnostics)

    monkeypatch.setattr(dataset.index, "add_diagnostics", spy)
    engine.validate(dataset)
    assert sorted(calls) == [1, 2]  # je Datei genau ein Aufruf (ein Commit)
    assert len(dataset.index.diagnostics(DiagnosticCategory.PROFILE_RULE)) >= 2


def test_xsd_violation_has_position_and_element(engine: ValidationEngine) -> None:
    dataset = dataset_of(("a.xml", ch20(root="Andere")))
    engine.validate(dataset)
    [item] = dataset.index.diagnostics(DiagnosticCategory.XSD)
    assert item.diagnostic.key is MessageKey.XSD_VIOLATION
    assert item.diagnostic.severity is Severity.ERROR
    assert item.diagnostic.params["step"] == "xsd"
    assert item.diagnostic.params["element"] == "Andere"
    assert item.diagnostic.position is not None
    assert item.diagnostic.position.line == 1


def general_findings(dataset: Dataset) -> list[tuple[MessageKey, object, int | None]]:
    items = dataset.index.diagnostics(DiagnosticCategory.PROFILE_RULE)
    return [
        (
            item.diagnostic.key,
            item.diagnostic.params["rule"],
            None if item.diagnostic.position is None else item.diagnostic.position.line,
        )
        for item in items
        if str(item.diagnostic.params.get("rule", "")).startswith("general_rules.")
    ]


def test_schematron_violations_use_rule_keys(engine: ValidationEngine) -> None:
    body = "\n<A order='1'/>\n  <B neu='1'/>"
    dataset = dataset_of(("a.xml", ch20(body)))
    engine.validate(dataset)
    assert general_findings(dataset) == [
        (MessageKey.SCHEMATRON_NO_ORDER_ATTRIBUTE, "general_rules.no_order_attribute", 2),
        (MessageKey.SCHEMATRON_VIOLATION, "general_rules.neu", 3),
    ]
    [unknown] = [
        d
        for d in dataset.index.diagnostics()
        if d.diagnostic.key is MessageKey.SCHEMATRON_VIOLATION
    ]
    assert unknown.diagnostic.params["detail"] == "neu"
    assert unknown.diagnostic.params["chapter"] == "src/03_xml_modelling.md"
    assert unknown.diagnostic.severity is Severity.ERROR


def test_file_of_another_version_is_not_checked(engine: ValidationEngine) -> None:
    data = (FIXTURES_DIR / "netex110_like.xml").read_bytes()
    dataset = dataset_of(("netex110_like.xml", data))
    summary = engine.validate(dataset)
    [outcome] = summary.files
    assert not outcome.checked
    assert outcome.reason is not None
    assert outcome.reason.key is MessageKey.VALIDATION_FILE_SKIPPED_PROFILE
    assert outcome.reason.params == {"status": "detected", "profile": "netex_1_10"}
    categories = {d.diagnostic.category for d in dataset.index.diagnostics()}
    assert categories <= {DiagnosticCategory.REFERENCE}


def undetected(attributes: str = "") -> bytes:
    """Datei ohne genügend Versionshinweise (Struktur fehlt, Wurzelattribut allein zählt nicht)."""
    root = f'<PublicationDelivery xmlns="{NAMESPACE}" {attributes}>'
    return f'{root}<A order="1"/></PublicationDelivery>'.encode()


@pytest.mark.parametrize(
    ("data", "status"),
    [(undetected(), "unknown"), (undetected('version="2.1"'), "ambiguous")],
)
def test_unrecognised_version_is_not_checked_by_default(
    engine: ValidationEngine, data: bytes, status: str
) -> None:
    dataset = dataset_of(("a.xml", data))
    summary = engine.validate(dataset)
    [outcome] = summary.files
    assert (outcome.checked, outcome.forced, summary.forced) == (False, False, False)
    assert dataset.detections[1].status == status


@pytest.mark.parametrize("attributes", ["", 'version="2.1"'])
def test_unrecognised_version_is_checked_on_request_and_marked(
    engine: ValidationEngine, attributes: str
) -> None:
    dataset = dataset_of(("a.xml", undetected(attributes)))
    summary = engine.validate(dataset, force_ch20=True)
    [outcome] = summary.files
    assert (outcome.checked, outcome.forced, summary.forced) == (True, True, True)
    assert outcome.reason is not None
    assert outcome.reason.key is MessageKey.VALIDATION_FORCED
    assert [(s.step_id, s.performed) for s in summary.steps] == [
        ("xsd", True),
        ("general_rules", True),
        ("ch_core_rules", True),
    ]
    assert counts(dataset)[
        (DiagnosticCategory.PROFILE_RULE, MessageKey.SCHEMATRON_NO_ORDER_ATTRIBUTE)
    ]


def test_forcing_never_checks_a_recognised_other_version_or_unreadable_file(
    engine: ValidationEngine,
) -> None:
    dataset = dataset_of(
        ("netex110_like.xml", (FIXTURES_DIR / "netex110_like.xml").read_bytes()),
        ("broken_xml.xml", (FIXTURES_DIR / "broken_xml.xml").read_bytes()),
        ("ok.xml", ch20()),
        ("u.xml", undetected()),
    )
    summary = engine.validate(dataset, force_ch20=True)
    assert [(f.checked, f.forced) for f in summary.files] == [
        (False, False),
        (False, False),
        (True, False),
        (True, True),
    ]
    assert summary.files[0].reason is not None
    assert summary.files[0].reason.key is MessageKey.VALIDATION_FILE_SKIPPED_PROFILE
    assert summary.files[1].reason is not None
    assert summary.files[1].reason.key is MessageKey.VALIDATION_FILE_SKIPPED_UNREADABLE
    assert summary.forced


def test_forced_run_is_replaced_by_a_normal_run(engine: ValidationEngine) -> None:
    dataset = dataset_of(("u.xml", undetected()))
    assert engine.validate(dataset, force_ch20=True).forced
    assert not engine.validate(dataset).forced


def test_unreadable_file_is_skipped(engine: ValidationEngine) -> None:
    dataset = dataset_of(("broken_xml.xml", (FIXTURES_DIR / "broken_xml.xml").read_bytes()))
    [outcome] = engine.validate(dataset).files
    assert outcome.reason is not None
    assert outcome.reason.key is MessageKey.VALIDATION_FILE_SKIPPED_UNREADABLE


def test_file_with_doctype_is_never_given_to_lxml(engine: ValidationEngine) -> None:
    dataset = dataset_of(("security_xxe.xml", (FIXTURES_DIR / "security_xxe.xml").read_bytes()))
    [outcome] = engine.validate(dataset).files
    assert not outcome.checked
    assert dataset.read_file(1)  # Inhalt liegt vor, wird aber nicht geprüft
    keys = {d.diagnostic.key for d in dataset.index.diagnostics()}
    assert keys == {MessageKey.XML_DOCTYPE_FORBIDDEN}


def test_mixed_dataset_checks_only_ch20_files(engine: ValidationEngine) -> None:
    dataset = dataset_of(
        ("a.xml", ch20("<A order='1'/>")),
        ("netex110_like.xml", (FIXTURES_DIR / "netex110_like.xml").read_bytes()),
    )
    summary = engine.validate(dataset)
    assert [(f.file_id, f.checked) for f in summary.files] == [(1, True), (2, False)]
    files = {d.file_id for d in dataset.index.diagnostics(DiagnosticCategory.PROFILE_RULE)}
    assert files == {1}


def test_revalidation_replaces_earlier_results(engine: ValidationEngine) -> None:
    dataset = dataset_of(("a.xml", ch20("<A order='1'/>")))
    engine.validate(dataset)
    first = counts(dataset)
    engine.validate(dataset)
    assert counts(dataset) == first


def test_missing_xsd_is_reported_and_other_steps_run(tmp_path: Path) -> None:
    engine = ValidationEngine(make_guide(tmp_path / "guide", xsd=False), COMMIT)
    assert not engine.preload()
    dataset = dataset_of(("a.xml", ch20("<A order='1'/>")))
    summary = engine.validate(dataset)
    assert {s.step_id: s.performed for s in summary.steps} == {
        "xsd": False,
        "general_rules": True,
        "ch_core_rules": True,
    }
    [xsd] = [s for s in summary.steps if s.step_id == "xsd"]
    assert xsd.reason is not None
    assert xsd.reason.key is MessageKey.VALIDATION_STEP_UNAVAILABLE
    assert xsd.reason.params == {"step": "xsd"}
    assert general_findings(dataset)


def test_missing_rules_are_reported(tmp_path: Path) -> None:
    engine = ValidationEngine(make_guide(tmp_path / "guide", rules=False), COMMIT)
    summary = engine.validate(dataset_of(("a.xml", ch20())))
    assert {s.step_id: s.performed for s in summary.steps}["general_rules"] is False


def test_file_that_lxml_rejects_is_reported(
    engine: ValidationEngine, monkeypatch: pytest.MonkeyPatch
) -> None:
    def reject(_data: bytes) -> ParsedDocument:
        raise NotCheckableError("Grund")

    monkeypatch.setattr(engine_module, "parse_safely", reject)
    dataset = dataset_of(("a.xml", ch20()))
    engine.validate(dataset)
    [item] = dataset.index.diagnostics(DiagnosticCategory.XSD)
    assert item.diagnostic.key is MessageKey.XSD_UNCHECKABLE
    assert item.diagnostic.params == {"detail": "Grund"}


def test_many_findings_are_truncated_with_a_note(engine: ValidationEngine) -> None:
    body = "".join("<A order='1'/>" for _ in range(520))
    dataset = dataset_of(("a.xml", ch20(body)))
    engine.validate(dataset)
    [note] = [
        d.diagnostic
        for d in dataset.index.diagnostics(DiagnosticCategory.PROFILE_RULE)
        if d.diagnostic.key is MessageKey.VALIDATION_TRUNCATED
    ]
    assert note.params == {"step": "general_rules", "count": 20}
    assert note.severity is Severity.INFO


# Am echten Guide-Stand


def validate_fixture(engine: ValidationEngine, name: str) -> Dataset:
    dataset = dataset_of((name, (FIXTURES_DIR / name).read_bytes()))
    engine.validate(dataset)
    return dataset


def problems(dataset: Dataset) -> list[tuple[str, str, str]]:
    own = (DiagnosticCategory.XSD, DiagnosticCategory.PROFILE_RULE)
    return [
        (item.diagnostic.category, item.diagnostic.key, str(item.diagnostic.params.get("rule", "")))
        for item in dataset.index.diagnostics()
        if item.diagnostic.category in own
    ]


def test_three_stops_is_valid_and_has_no_core_rule_violation(
    guide_engine: ValidationEngine,
) -> None:
    assert problems(validate_fixture(guide_engine, "ch20_three_stops.xml")) == []


def test_calls_violate_the_core_rule_with_source(guide_engine: ValidationEngine) -> None:
    dataset = validate_fixture(guide_engine, "ch20_calls.xml")
    assert ("profile_rule", "core.forbidden_present", "CH-SJ-13") in problems(dataset)
    [item] = [
        d for d in dataset.index.diagnostics() if d.diagnostic.params.get("rule") == "CH-SJ-13"
    ]
    assert item.diagnostic.params["source"] == "templates/ServiceJourney.xml Z. 145-153"


def test_duplicate_id_gives_xsd_errors(guide_engine: ValidationEngine) -> None:
    dataset = validate_fixture(guide_engine, "ch20_duplicate_id.xml")
    xsd = [p for p in problems(dataset) if p[0] == "xsd"]
    assert xsd
    assert all(key == "xsd.violation" for _, key, _ in xsd)
    detail = [
        d.diagnostic.params["detail"] for d in dataset.index.diagnostics(DiagnosticCategory.XSD)
    ]
    assert any("Duplicate key-sequence" in str(text) for text in detail)


def test_other_valid_fixtures_have_no_xsd_errors(guide_engine: ValidationEngine) -> None:
    for name in (
        "ch20_offers.xml",
        "ch20_midnight.xml",
        "ch20_network_offer.xml",
        "ch20_site_offer.xml",
        "ch20_utc_departure.xml",
    ):
        dataset = validate_fixture(guide_engine, name)
        assert not dataset.index.diagnostics(DiagnosticCategory.XSD), name


def test_guide_examples_have_no_order_violations(
    guide_engine: ValidationEngine, guide_path: Path
) -> None:
    """Seit Guide `d0a8e6d` enthalten die Beispiele kein `order`-Attribut mehr (vorher 121 Befunde).

    Dass die Regel `no_order_attribute` weiterhin greift, belegen die synthetischen Tests oben.
    """
    for file in sorted(examples_dir(guide_path).glob("*.xml")):
        dataset = dataset_of((file.name, file.read_bytes()))
        guide_engine.validate(dataset)
        assert not dataset.index.diagnostics(DiagnosticCategory.XSD), file.name
        orders = [
            d
            for d in dataset.index.diagnostics(DiagnosticCategory.PROFILE_RULE)
            if d.diagnostic.key is MessageKey.SCHEMATRON_NO_ORDER_ATTRIBUTE
        ]
        assert orders == [], file.name
