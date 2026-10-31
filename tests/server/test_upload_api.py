"""Eigene Dateien: Hochladen, Versionserkennung, Validierung, Schliessen und Sicherheit."""

from __future__ import annotations

import io
import stat
import zipfile
from collections.abc import Iterator
from dataclasses import replace
from pathlib import Path
from typing import Any, Protocol

import httpx2
import pytest
from fastapi.testclient import TestClient

from app.core.config import ZipLimits, load_config
from app.core.guide.layout import ANNEX_INDEX_FILE
from app.core.guide.status import inspect_guide
from app.core.validation.engine import ValidationEngine
from app.server.app import create_app
from app.server.datasets import MAX_OPEN_DATASETS
from app.server.runtime import Runtime
from tests.support import FIXTURES_DIR, PROJECT_ROOT, REF_TARGETS, SHA_A

BASE_URL = "http://127.0.0.1"
FILES = "files"
SECRET = (FIXTURES_DIR / "xxe_secret.txt").read_text(encoding="utf-8").strip()
INDEX = "\n".join(
    [
        "- ServiceJourney: [SJ](site/tables/SJ.html), [08_timetable](08_timetable.html)",
        "- ScheduledStopPoint: [x](05_stops.html), [y](08_timetable.html)",
    ]
)


def fixture(name: str) -> bytes:
    return (FIXTURES_DIR / name).read_bytes()


def zip_of(entries: dict[str, bytes], *, symlink: str | None = None) -> bytes:
    buffer = io.BytesIO()
    with zipfile.ZipFile(buffer, "w", zipfile.ZIP_DEFLATED) as archive:
        for name, data in entries.items():
            info = zipfile.ZipInfo(name)
            info.compress_type = zipfile.ZIP_DEFLATED
            if name == symlink:
                info.external_attr = (stat.S_IFLNK | 0o777) << 16
            archive.writestr(info, data)
    return buffer.getvalue()


def upload(client: TestClient, *items: tuple[str, bytes]) -> httpx2.Response:
    return client.post("/api/datasets/upload", files=[(FILES, (n, d)) for n, d in items])


class ClientFactory(Protocol):
    def __call__(self, limits: ZipLimits | None = None) -> TestClient: ...


@pytest.fixture
def work_dir(tmp_path: Path) -> Path:
    return tmp_path / "work"


@pytest.fixture
def make_client(
    synthetic_guide: Path, tmp_path: Path, work_dir: Path, guide_engine: ValidationEngine
) -> ClientFactory:
    def factory(limits: ZipLimits | None = None) -> TestClient:
        index = synthetic_guide.joinpath(*ANNEX_INDEX_FILE.parts)
        index.parent.mkdir(parents=True, exist_ok=True)
        index.write_text(INDEX, encoding="utf-8")
        config = load_config(PROJECT_ROOT)
        settings = replace(config.settings, guide_path=synthetic_guide)
        if limits is not None:
            settings = replace(settings, zip_limits=limits)
        config = replace(config, settings=settings)
        guide = inspect_guide(synthetic_guide, tmp_path / "t.json", REF_TARGETS)
        runtime = Runtime(config, guide, work_dir, engine=guide_engine)
        return TestClient(create_app(runtime, None), base_url=BASE_URL)

    return factory


@pytest.fixture
def client(make_client: ClientFactory) -> TestClient:
    return make_client()


def sessions(work_dir: Path) -> list[Path]:
    return sorted(work_dir.iterdir()) if work_dir.is_dir() else []


def diagnostics(client: TestClient, dataset_id: str, category: str | None = None) -> list[Any]:
    query = "" if category is None else f"?category={category}"
    response = client.get(f"/api/datasets/{dataset_id}/diagnostics{query}")
    assert response.status_code == 200
    result: list[Any] = response.json()
    return result


def test_upload_one_xml_file(client: TestClient, work_dir: Path) -> None:
    response = upload(client, ("ch20_three_stops.xml", fixture("ch20_three_stops.xml")))
    assert response.status_code == 200
    data = response.json()
    [file] = data["files"]
    assert file["name"] == "ch20_three_stops.xml"
    assert file["readable"] is True
    assert file["detection"]["status"] == "detected"
    assert file["detection"]["profile"] == "ch_2_0"
    assert {r["evidence"] for r in file["detection"]["reasons"]} >= {"ch_2_0", "neutral"}
    assert data["validation"] is None
    assert data == client.get(f"/api/datasets/{data['id']}").json()
    [session] = sessions(work_dir)
    assert (session / "files" / "ch20_three_stops.xml").is_file()
    assert client.get(f"/api/datasets/{data['id']}/journeys").json()


def test_close_removes_the_files(client: TestClient, work_dir: Path) -> None:
    dataset_id = upload(client, ("a.xml", fixture("ch20_three_stops.xml"))).json()["id"]
    assert len(sessions(work_dir)) == 1
    assert client.delete(f"/api/datasets/{dataset_id}").status_code == 204
    assert sessions(work_dir) == []
    assert client.get(f"/api/datasets/{dataset_id}").status_code == 404
    assert client.delete(f"/api/datasets/{dataset_id}").status_code == 404
    assert client.delete("/api/datasets/zu-kurz").status_code == 404


def test_upload_several_xml_files_resolves_references(client: TestClient) -> None:
    data = upload(
        client,
        ("ch20_network_offer.xml", fixture("ch20_network_offer.xml")),
        ("ch20_site_offer.xml", fixture("ch20_site_offer.xml")),
    ).json()
    assert [f["name"] for f in data["files"]] == ["ch20_network_offer.xml", "ch20_site_offer.xml"]
    assert all(f["detection"]["profile"] == "ch_2_0" for f in data["files"])
    unresolved = [
        d for d in diagnostics(client, data["id"], "reference") if d["severity"] != "info"
    ]
    assert unresolved == []


def test_upload_zip(client: TestClient, work_dir: Path) -> None:
    archive = zip_of(
        {
            "NETWORK_OFFER.xml": fixture("ch20_network_offer.xml"),
            "SITE_OFFER.xml": fixture("ch20_site_offer.xml"),
            "Workflow/README.csv": b"a;b",
        }
    )
    data = upload(client, ("lieferung.zip", archive)).json()
    names = [f["name"] for f in data["files"]]
    assert names[:2] == ["NETWORK_OFFER.xml", "SITE_OFFER.xml"]
    skipped = [
        d for d in diagnostics(client, data["id"], "file") if d["key"] == "zip.entries_skipped"
    ]
    assert skipped[0]["severity"] == "info"
    assert skipped[0]["params"]["count"] == 1
    client.delete(f"/api/datasets/{data['id']}")
    assert sessions(work_dir) == []


def test_validate_valid_file_has_no_findings(
    client: TestClient, guide_engine: ValidationEngine
) -> None:
    dataset_id = upload(client, ("a.xml", fixture("ch20_three_stops.xml"))).json()["id"]
    response = client.post(f"/api/datasets/{dataset_id}/validate")
    assert response.status_code == 200
    data = response.json()
    assert data["diagnosticCounts"] == {"error": 0, "warning": 0, "info": 0}
    validation = data["validation"]
    assert validation["guideCommit"] == guide_engine.guide_commit
    assert validation["guideCommit"] is not None
    assert [(s["id"], s["performed"]) for s in validation["steps"]] == [
        ("xsd", True),
        ("general_rules", True),
        ("ch_core_rules", True),
    ]
    assert validation["files"] == [{"fileId": 1, "checked": True, "reason": None}]
    assert data == client.get(f"/api/datasets/{dataset_id}").json()


def test_validate_reports_core_rule_with_source_and_guide_link(client: TestClient) -> None:
    dataset_id = upload(client, ("calls.xml", fixture("ch20_calls.xml"))).json()["id"]
    client.post(f"/api/datasets/{dataset_id}/validate")
    items = diagnostics(client, dataset_id, "profile_rule")
    [calls] = [d for d in items if d["params"].get("rule") == "CH-SJ-13"]
    assert calls["severity"] == "error"
    assert calls["key"] == "core.forbidden_present"
    assert calls["params"]["source"] == "templates/ServiceJourney.xml Z. 145-153"
    assert calls["line"] is not None
    assert calls["guideLink"].endswith(f"/blob/{SHA_A}/src/08_timetable.md")
    assert "github.com/openTdataCH/netexRealisationGuideSwitzerland" in calls["guideLink"]
    xml = client.get(
        f"/api/datasets/{dataset_id}/xml", params={"file": 1, "line": calls["line"], "column": 1}
    )
    assert xml.status_code == 200
    assert "calls" in xml.json()["text"]


def test_validate_duplicate_id_gives_xsd_errors(client: TestClient) -> None:
    dataset_id = upload(client, ("dup.xml", fixture("ch20_duplicate_id.xml"))).json()["id"]
    data = client.post(f"/api/datasets/{dataset_id}/validate").json()
    xsd = diagnostics(client, dataset_id, "xsd")
    assert xsd
    assert all(d["severity"] == "error" and d["key"] == "xsd.violation" for d in xsd)
    assert data["diagnosticCounts"]["error"] >= len(xsd)
    assert any("Duplicate key-sequence" in d["params"]["detail"] for d in xsd)
    # XSD-Befunde nennen kein Kapitel: der Link kommt aus dem Index (erstes Kapitel des Elements).
    linked = [d for d in xsd if d["params"]["element"] == "ScheduledStopPoint"]
    assert linked
    assert linked[0]["guideLink"].endswith(f"/blob/{SHA_A}/src/05_stops.md")


def test_order_violation_has_position_and_link(client: TestClient) -> None:
    text = fixture("ch20_three_stops.xml").decode()
    changed = text.replace(
        "<StopPointInJourneyPattern ", '<StopPointInJourneyPattern order="1" ', 1
    )
    assert changed != text
    dataset_id = upload(client, ("o.xml", changed.encode())).json()["id"]
    client.post(f"/api/datasets/{dataset_id}/validate")
    [order] = [
        d
        for d in diagnostics(client, dataset_id, "profile_rule")
        if d["key"] == "schematron.no_order_attribute"
    ]
    assert order["params"]["element"] == "StopPointInJourneyPattern"
    assert order["params"]["rule"] == "general_rules.no_order_attribute"
    assert order["line"] == changed[: changed.index('order="1"')].count("\n") + 1
    assert order["guideLink"].endswith(f"/blob/{SHA_A}/src/03_xml_modelling.md")


def test_110_file_is_detected_and_not_checked(client: TestClient) -> None:
    data = upload(client, ("netex110_like.xml", fixture("netex110_like.xml"))).json()
    detection = data["files"][0]["detection"]
    assert (detection["status"], detection["profile"]) == ("detected", "netex_1_10")
    validated = client.post(f"/api/datasets/{data['id']}/validate").json()
    [outcome] = validated["validation"]["files"]
    assert outcome["checked"] is False
    assert outcome["reason"]["key"] == "validation.file_skipped_profile"
    assert diagnostics(client, data["id"], "xsd") == []
    assert diagnostics(client, data["id"], "profile_rule") == []
    assert client.get(f"/api/datasets/{data['id']}/objects").json()["total"] > 0


def test_validation_can_be_repeated(client: TestClient) -> None:
    dataset_id = upload(client, ("calls.xml", fixture("ch20_calls.xml"))).json()["id"]
    first = client.post(f"/api/datasets/{dataset_id}/validate").json()
    second = client.post(f"/api/datasets/{dataset_id}/validate").json()
    assert first["diagnosticCounts"] == second["diagnosticCounts"]


def test_validate_unknown_dataset(client: TestClient) -> None:
    assert client.post("/api/datasets/gibtesnicht1234567/validate").status_code == 404


def test_upload_requires_files(client: TestClient) -> None:
    assert client.post("/api/datasets/upload").status_code in {413, 422}
    response = client.post("/api/datasets/upload", data={"x": "y"})
    assert response.status_code == 422


def test_unsupported_and_cleaned_names_become_diagnostics(
    client: TestClient, work_dir: Path
) -> None:
    data = upload(
        client, ("../../a b?.xml", fixture("ch20_three_stops.xml")), ("evil.exe", b"MZ")
    ).json()
    assert data["files"][0]["name"] == "a b_.xml"
    keys = {d["key"] for d in diagnostics(client, data["id"], "file")}
    assert keys == {"file.name_changed", "file.type_unsupported"}
    assert list(work_dir.parent.glob("*.xml")) == []


def test_too_many_files(make_client: ClientFactory) -> None:
    client = make_client(ZipLimits(max_files=2))
    response = upload(client, *[(f"{n}.xml", b"<a/>") for n in range(3)])
    assert response.status_code == 413
    assert response.json() == {"error": {"key": "error.payload_too_large", "params": {}}}


def test_upload_too_large_is_rejected_before_reading(
    make_client: ClientFactory, work_dir: Path
) -> None:
    client = make_client(ZipLimits(max_total_bytes=1000))
    response = upload(client, ("a.xml", b"<a>" + b"x" * (2 * 1024 * 1024) + b"</a>"))
    assert response.status_code == 413
    assert response.json()["error"]["key"] == "error.payload_too_large"
    assert response.headers["Cache-Control"] == "no-store"
    assert sessions(work_dir) == []


def test_upload_without_content_length_is_rejected(client: TestClient) -> None:
    def chunks() -> Iterator[bytes]:
        yield b"--x\r\n"

    response = client.post(
        "/api/datasets/upload",
        content=chunks(),
        headers={"Content-Type": "multipart/form-data; boundary=x"},
    )
    assert response.status_code == 413


def test_single_file_over_the_limit_becomes_a_diagnostic(make_client: ClientFactory) -> None:
    client = make_client(ZipLimits(max_file_bytes=50))
    data = upload(client, ("gross.xml", fixture("ch20_three_stops.xml"))).json()
    assert data["files"][0]["readable"] is False
    [item] = diagnostics(client, data["id"], "file")
    assert item["key"] == "file.too_large"
    assert item["params"] == {"limit": 50}


# Sicherheit


def test_xxe_and_doctype_are_rejected_without_leaking(client: TestClient) -> None:
    response = upload(client, ("xxe.xml", fixture("security_xxe.xml")))
    assert response.status_code == 200
    data = response.json()
    assert data["files"][0]["readable"] is False
    [item] = diagnostics(client, data["id"], "xml_syntax")
    assert item["key"] == "xml.doctype_forbidden"
    validated = client.post(f"/api/datasets/{data['id']}/validate")
    assert validated.status_code == 200
    assert validated.json()["validation"]["files"][0]["checked"] is False
    everything = [
        response.text,
        validated.text,
        client.get(f"/api/datasets/{data['id']}/diagnostics").text,
        client.get(f"/api/datasets/{data['id']}/objects").text,
        client.get(f"/api/datasets/{data['id']}/xml", params={"file": 1, "line": 1}).text,
    ]
    assert all(SECRET not in text for text in everything)


def test_zip_slip_entries_are_rejected(client: TestClient, tmp_path: Path, work_dir: Path) -> None:
    archive = zip_of(
        {
            "../evil.xml": fixture("ch20_three_stops.xml"),
            "/abs/evil2.xml": fixture("ch20_three_stops.xml"),
            "gut.xml": fixture("ch20_three_stops.xml"),
        }
    )
    data = upload(client, ("z.zip", archive)).json()
    assert [f["name"] for f in data["files"] if f["readable"]] == ["gut.xml"]
    items = diagnostics(client, data["id"], "file")
    assert [d["key"] for d in items] == ["zip.unsafe_path", "zip.unsafe_path"]
    assert not (tmp_path / "evil.xml").exists()
    assert not (work_dir / "evil.xml").exists()
    assert not list(tmp_path.rglob("evil2.xml"))


def test_zip_symlink_is_rejected(client: TestClient) -> None:
    archive = zip_of({"link.xml": b"/etc/passwd", "gut.xml": b"<a/>"}, symlink="link.xml")
    data = upload(client, ("z.zip", archive)).json()
    assert [d["key"] for d in diagnostics(client, data["id"], "file")] == ["zip.symlink"]
    assert [f["name"] for f in data["files"] if f["readable"]] == ["gut.xml"]


def test_zip_limits_are_enforced(make_client: ClientFactory) -> None:
    limits = ZipLimits(max_total_bytes=3_000_000, max_file_bytes=2_000_000, max_files=3)
    client = make_client(limits)
    bomb = b"<a>" + b"0" * 1_500_000 + b"</a>"
    cases = {
        "zip.compression_ratio": zip_of({"bomb.xml": bomb}),
        "zip.too_many_files": zip_of({f"{n}.xml": b"<a/>" for n in range(4)}),
        "zip.unreadable": b"kein zip",
    }
    for key, archive in cases.items():
        data = upload(client, ("z.zip", archive)).json()
        assert key in {d["key"] for d in diagnostics(client, data["id"], "file")}, key
        assert not [f for f in data["files"] if f["readable"]]


def test_html_in_xml_values_is_returned_as_data(client: TestClient) -> None:
    text = fixture("ch20_three_stops.xml").decode()
    payload = "&lt;img src=x onerror=alert(1)&gt;&lt;script&gt;alert(2)&lt;/script&gt;"
    changed = text.replace("<Name>Synthetische Bahn</Name>", f"<Name>{payload}</Name>", 1)
    assert changed != text
    data = upload(client, ("h.xml", changed.encode())).json()
    response = client.get(f"/api/datasets/{data['id']}/objects", params={"type": "Operator"})
    assert response.headers["Content-Type"] == "application/json"
    assert response.headers["X-Content-Type-Options"] == "nosniff"
    [operator] = response.json()["items"]
    assert operator["label"] == "<img src=x onerror=alert(1)><script>alert(2)</script>"


def test_invalid_ids_are_rejected(client: TestClient) -> None:
    for bad in ("..%2F..%2Fetc", "a b", "x" * 100):
        assert client.delete(f"/api/datasets/{bad}").status_code == 404
        assert client.post(f"/api/datasets/{bad}/validate").status_code == 404


def test_api_accepts_no_paths(client: TestClient) -> None:
    response = client.post("/api/datasets", json={"example": "/etc/passwd"})
    assert response.status_code == 404
    response = client.post("/api/datasets/upload", json={"path": "/etc/passwd"})
    assert response.status_code == 422


# Arbeitsverzeichnis


def test_old_datasets_are_cleaned_up_when_over_the_limit(
    client: TestClient, work_dir: Path
) -> None:
    first = upload(client, ("a.xml", fixture("ch20_three_stops.xml"))).json()["id"]
    for _ in range(MAX_OPEN_DATASETS):
        upload(client, ("a.xml", fixture("ch20_three_stops.xml")))
    assert len(sessions(work_dir)) == MAX_OPEN_DATASETS
    assert client.get(f"/api/datasets/{first}").status_code == 404


def test_start_removes_leftovers(make_client: ClientFactory, work_dir: Path) -> None:
    leftover = work_dir / ("L" * 22)
    leftover.mkdir(parents=True)
    (leftover / "alt.xml").write_text("<a/>", encoding="utf-8")
    make_client()
    assert not leftover.exists()


def test_failed_upload_leaves_no_files(
    client: TestClient, work_dir: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    def explode(*_args: object, **_kwargs: object) -> None:
        raise ValueError("kaputt")

    monkeypatch.setattr("app.server.dataset_routes.open_dataset", explode)
    with pytest.raises(ValueError, match="kaputt"):
        upload(client, ("a.xml", fixture("ch20_three_stops.xml")))
    assert sessions(work_dir) == []
