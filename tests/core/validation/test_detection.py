"""Versionserkennung: Gewichtung der Hinweise, Guide-Beispiele und 1.10-Nachbildung."""

from __future__ import annotations

from pathlib import Path

import pytest

from app.core.guide.examples import examples_dir
from app.core.messages import MessageKey
from app.core.reader.xml_reader import read_xml
from app.core.validation.detection import (
    DetectionStatus,
    Evidence,
    ProfileVersion,
    VersionDetection,
    detect_version,
)
from tests.support import FIXTURES_DIR

NAMESPACE = "http://www.netex.org.uk/netex"
XSI = "http://www.w3.org/2001/XMLSchema-instance"


def detect_bytes(name: str, data: bytes) -> VersionDetection:
    return detect_version(read_xml(name, data))


def detect_fixture(name: str) -> VersionDetection:
    return detect_bytes(name, (FIXTURES_DIR / name).read_bytes())


def root(attributes: str = "", body: str = "", namespace: str = NAMESPACE) -> bytes:
    head = f'<PublicationDelivery xmlns="{namespace}" xmlns:xsi="{XSI}" {attributes}>'
    return f"{head}{body}</PublicationDelivery>".encode()


def reason_keys(detection: VersionDetection) -> list[MessageKey]:
    return [reason.key for reason in detection.reasons]


def test_ch20_fixture_is_detected_with_reasons() -> None:
    detection = detect_fixture("ch20_three_stops.xml")
    assert detection.status is DetectionStatus.DETECTED
    assert detection.profile is ProfileVersion.CH_2_0
    assert detection.checkable
    assert MessageKey.VERSION_ATTRIBUTE_20 in reason_keys(detection)
    assert MessageKey.VERSION_STRUCTURE_PATTERN in reason_keys(detection)


def test_netex_110_like_is_detected_as_110() -> None:
    detection = detect_fixture("netex110_like.xml")
    assert detection.status is DetectionStatus.DETECTED
    assert detection.profile is ProfileVersion.NETEX_1_10
    assert not detection.checkable
    keys = reason_keys(detection)
    assert MessageKey.VERSION_ATTRIBUTE_110 in keys
    assert MessageKey.VERSION_SCHEMA_LOCATION_110 in keys
    assert MessageKey.VERSION_COMMENT_PROFILE in keys
    assert MessageKey.VERSION_STRUCTURE_CALLS in keys


def test_ch20_with_forbidden_calls_stays_ch20() -> None:
    """`calls` sind in 2.0 verboten, kippen eine klare 2.0-Datei aber nicht."""
    detection = detect_fixture("ch20_calls.xml")
    assert detection.profile is ProfileVersion.CH_2_0
    assert MessageKey.VERSION_STRUCTURE_CALLS in reason_keys(detection)


def test_root_version_alone_does_not_decide() -> None:
    detection = detect_bytes("x.xml", root('version="2.1"'))
    assert detection.status is DetectionStatus.AMBIGUOUS
    assert detection.profile is None
    assert not detection.checkable
    assert detect_bytes("y.xml", root('version="1.10"')).status is DetectionStatus.AMBIGUOUS


def test_contradiction_is_ambiguous() -> None:
    body = "<ServiceJourneyPattern/><TimeDemandType/>"
    detection = detect_bytes("x.xml", root('version="1.10"', body))
    assert detection.status is DetectionStatus.AMBIGUOUS


def test_old_version_attribute_is_neutral() -> None:
    body = "<ServiceJourneyPattern/><TimeDemandType/>"
    attributes = (
        'version="1.09" xsi:schemaLocation="http://www.netex.org.uk/netex '
        '../../xsd/xsd/NeTEx_publication.xsd"'
    )
    detection = detect_bytes("01_example.xml", root(attributes, body))
    assert detection.profile is ProfileVersion.CH_2_0
    assert MessageKey.VERSION_ATTRIBUTE_OTHER in reason_keys(detection)
    assert MessageKey.VERSION_SCHEMA_LOCATION_GUIDE in reason_keys(detection)


def test_file_type_in_name_counts_as_weak_hint() -> None:
    detection = detect_bytes("x_SITE_OFFER.xml", root('version="2.1"'))
    assert detection.profile is ProfileVersion.CH_2_0
    assert MessageKey.VERSION_FILE_NAME_TYPE in reason_keys(detection)


def test_schema_location_variants() -> None:
    def keys(location: str) -> list[MessageKey]:
        attributes = f'xsi:schemaLocation="{NAMESPACE} {location}"'
        return reason_keys(detect_bytes("x.xml", root(attributes)))

    assert MessageKey.VERSION_SCHEMA_LOCATION_20 in keys("http://netex.uk/schema/2.1/xsd/a.xsd")
    assert MessageKey.VERSION_SCHEMA_LOCATION_OTHER in keys("http://example.org/a.xsd")


def test_no_version_hint_is_unknown() -> None:
    detection = detect_bytes("x.xml", root())
    assert detection.status is DetectionStatus.UNKNOWN
    assert MessageKey.VERSION_ATTRIBUTE_MISSING in reason_keys(detection)


def test_other_namespace_is_unknown_and_explained() -> None:
    detection = detect_bytes("x.xml", root('version="2.1"', namespace="http://example.org/other"))
    assert detection.status is DetectionStatus.UNKNOWN
    assert reason_keys(detection) == [MessageKey.VERSION_NOT_NETEX]


def test_unreadable_file_is_unknown_without_reasons() -> None:
    detection = detect_fixture("broken_xml.xml")
    assert detection.status in {DetectionStatus.UNKNOWN, DetectionStatus.AMBIGUOUS}
    assert not detection.checkable
    empty = detect_bytes("leer.xml", b"")
    assert empty.status is DetectionStatus.UNKNOWN
    assert empty.reasons == ()


def test_evidence_is_labelled() -> None:
    detection = detect_fixture("netex110_like.xml")
    evidences = {reason.evidence for reason in detection.reasons}
    assert evidences == {Evidence.NEUTRAL, Evidence.NETEX_1_10}


def test_every_guide_example_is_ch20(guide_path: Path) -> None:
    """Auch die Beispiele mit `version="1.09"` (01, 20) und ohne Attribut (08)."""
    files = sorted(examples_dir(guide_path).glob("*.xml"))
    assert len(files) >= 22
    for file in files:
        detection = detect_bytes(file.name, file.read_bytes())
        assert detection.profile is ProfileVersion.CH_2_0, file.name


@pytest.mark.parametrize(
    "name", ["01_NeTEx_Spiez_Interlaken_Ost.xml", "20_NeTEx_Interlaken_Spiez_Formation.xml"]
)
def test_examples_with_old_version_are_explained(guide_path: Path, name: str) -> None:
    detection = detect_bytes(name, (examples_dir(guide_path) / name).read_bytes())
    assert MessageKey.VERSION_ATTRIBUTE_OTHER in reason_keys(detection)
