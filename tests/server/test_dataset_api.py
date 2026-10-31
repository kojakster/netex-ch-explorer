from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient

from app.core.config import load_config
from app.core.dataset import SourceFile, open_dataset
from app.core.guide.status import inspect_guide
from app.server.app import create_app
from app.server.datasets import DatasetRegistry, object_id, parse_object_id
from app.server.runtime import Runtime
from tests.support import FIXTURES_DIR, PROJECT_ROOT, REF_TARGETS

BASE_URL = "http://127.0.0.1"


@pytest.fixture
def client(synthetic_guide: Path, tmp_path: Path) -> TestClient:
    config = load_config(PROJECT_ROOT)
    config = replace(config, settings=replace(config.settings, guide_path=synthetic_guide))
    runtime = Runtime(
        config=config, guide=inspect_guide(synthetic_guide, tmp_path / "t.json", REF_TARGETS)
    )
    return TestClient(create_app(runtime, None), base_url=BASE_URL)


def open_example(client: TestClient, name: str = "ch20_three_stops.xml") -> dict[str, Any]:
    response = client.post("/api/datasets", json={"example": name})
    assert response.status_code == 200
    data: dict[str, Any] = response.json()
    return data


def test_guide_lists_examples(client: TestClient) -> None:
    examples = client.get("/api/guide").json()["examples"]
    assert [e["name"] for e in examples] == [
        "broken_xml.xml",
        "ch20_midnight.xml",
        "ch20_three_stops.xml",
    ]
    assert examples[0] == {
        "name": "broken_xml.xml",
        "title": "Kaputt",
        "result": "unreadable",
        "counts": {"error": 1},
        "change": "untested",
    }


def test_open_example(client: TestClient) -> None:
    data = open_example(client)
    assert data["files"] == [
        {
            "id": 1,
            "name": "ch20_three_stops.xml",
            "size": (FIXTURES_DIR / "ch20_three_stops.xml").stat().st_size,
            "sha256": data["files"][0]["sha256"],
            "readable": True,
            "elements": 113,
            "objects": 33,
        }
    ]
    assert data["diagnosticCounts"] == {"error": 0, "warning": 0, "info": 0}
    assert {"name": "Quay", "count": 3} in data["objectTypes"]
    assert data == client.get(f"/api/datasets/{data['id']}").json()


@pytest.mark.parametrize("name", ["../README.md", "README.md", "/etc/passwd", "fehlt.xml"])
def test_open_rejects_unknown_names(client: TestClient, name: str) -> None:
    response = client.post("/api/datasets", json={"example": name})
    assert response.status_code == 404
    assert response.json() == {"error": {"key": "error.not_found", "params": {}}}


def test_open_rejects_invalid_body(client: TestClient) -> None:
    assert client.post("/api/datasets", json={"example": ""}).status_code == 422
    assert client.post("/api/datasets", json={"path": "/etc"}).status_code == 422


def test_journeys(client: TestClient) -> None:
    dataset_id = open_example(client)["id"]
    [journey] = client.get(f"/api/datasets/{dataset_id}/journeys").json()
    assert journey["object"]["xmlId"] == "ch:1:sjyid:SYN:1"
    assert journey["object"]["colorKey"] == "TimetableFrame"
    assert journey["trainNumbers"][0]["text"] == "1"
    assert journey["line"]["status"] == "found"
    assert journey["lastStop"]["text"] == "Synthetisch C"


def test_search_detail_and_xml(client: TestClient) -> None:
    dataset_id = open_example(client)["id"]
    search = client.get(
        f"/api/datasets/{dataset_id}/objects", params={"type": "Quay", "q": "SYN2"}
    ).json()
    assert search["total"] == 1
    [quay] = search["items"]
    assert (quay["name"], quay["xmlId"], quay["colorKey"]) == (
        "Quay",
        "ch:1:sloid:SYN2:0:1",
        "SiteFrame",
    )
    assert quay["frame"]["name"] == "SiteFrame"
    detail = client.get(f"/api/objects/{quay['id']}").json()
    assert detail["path"].endswith("/StopPlace[2]/quays/Quay")
    assert detail["attributes"] == {"id": "ch:1:sloid:SYN2:0:1", "version": "1"}
    [public_code] = detail["properties"]
    assert (public_code["name"], public_code["text"]) == ("PublicCode", "2")
    window = client.get(f"/api/objects/{quay['id']}/xml").json()
    marked = window["text"][window["focusFrom"] : window["focusTo"]]
    assert marked.startswith("<Quay") and marked.endswith("</Quay>")
    assert window["frames"][0]["colorKey"] == "CompositeFrame"
    child = client.get(f"/api/objects/{public_code['id']}/xml").json()
    assert child["text"][child["focusFrom"] : child["focusTo"]] == "<PublicCode>2</PublicCode>"


def test_search_limits(client: TestClient) -> None:
    dataset_id = open_example(client)["id"]
    url = f"/api/datasets/{dataset_id}/objects"
    assert client.get(url, params={"limit": 201}).status_code == 422
    assert client.get(url, params={"offset": -1}).status_code == 422
    assert client.get(url, params={"q": "x" * 201}).status_code == 422
    assert client.get(url, params={"offset": 10**20}).status_code == 422
    xml_url = f"/api/datasets/{dataset_id}/xml"
    assert client.get(xml_url, params={"file": 10**20, "line": 1}).status_code == 422
    page = client.get(url, params={"limit": 5, "offset": 5}).json()
    assert len(page["items"]) == 5


def test_diagnostics_and_xml_at_position(client: TestClient) -> None:
    dataset_id = open_example(client, "broken_xml.xml")["id"]
    [diagnostic] = client.get(f"/api/datasets/{dataset_id}/diagnostics").json()
    assert diagnostic["key"] == "xml.syntax_error"
    assert diagnostic["category"] == "xml_syntax"
    assert diagnostic["line"] == 48
    params = {"file": 1, "line": diagnostic["line"], "column": diagnostic["column"]}
    window = client.get(f"/api/datasets/{dataset_id}/xml", params=params).json()
    assert window["text"][window["focusFrom"] : window["focusTo"]] == "N"
    filtered = client.get(
        f"/api/datasets/{dataset_id}/diagnostics", params={"severity": "info"}
    ).json()
    assert filtered == []
    assert (
        client.get(f"/api/datasets/{dataset_id}/xml", params={"file": 7, "line": 1}).status_code
        == 404
    )
    assert (
        client.get(f"/api/datasets/{dataset_id}/diagnostics", params={"category": "x"}).status_code
        == 422
    )


@pytest.mark.parametrize(
    "path",
    [
        "/api/datasets/unbekanntunbekanntunbekannt",
        "/api/datasets/kurz/journeys",
        "/api/objects/keine-id",
        "/api/objects/unbekanntunbekanntunbekannt.5/xml",
    ],
)
def test_unknown_ids(client: TestClient, path: str) -> None:
    assert client.get(path).status_code == 404


def test_unknown_element_in_known_dataset(client: TestClient) -> None:
    dataset_id = open_example(client)["id"]
    assert client.get(f"/api/objects/{dataset_id}.99999").status_code == 404
    assert client.get(f"/api/objects/{dataset_id}.99999/xml").status_code == 404


def test_registry_evicts_oldest() -> None:
    registry = DatasetRegistry(max_open=2)
    data = (FIXTURES_DIR / "ch20_site_offer.xml").read_bytes()
    datasets = [open_dataset([SourceFile("s.xml", data)], (), REF_TARGETS) for _ in range(3)]
    ids = [registry.add(dataset) for dataset in datasets]
    assert registry.get(ids[0]) is None
    # Wer den verdrängten Datensatz noch hält, kann ihn weiter benutzen.
    assert datasets[0].index.files()[0].name == "s.xml"
    assert registry.get(ids[1]) is not None
    assert registry.get("../etc") is None
    registry.close_all()
    assert registry.get(ids[2]) is None


def test_object_ids() -> None:
    assert parse_object_id(object_id("A" * 22, 17)) == ("A" * 22, 17)
    for value in ("A" * 22, "A" * 22 + ".0", "A" * 22 + ".x", "kurz.1", "A" * 22 + ".1.2"):
        assert parse_object_id(value) is None


def test_xml_offsets_for_browser_with_crlf(tmp_path: Path, synthetic_guide: Path) -> None:
    crlf = (FIXTURES_DIR / "ch20_three_stops.xml").read_text(encoding="utf-8").replace("\n", "\r\n")
    crlf = crlf.replace("Synthetisch A", "Synthetisch \U0001f686 A")
    (synthetic_guide / "src" / "examples" / "ch20_three_stops.xml").write_bytes(crlf.encode())
    config = load_config(PROJECT_ROOT)
    config = replace(config, settings=replace(config.settings, guide_path=synthetic_guide))
    runtime = Runtime(
        config=config, guide=inspect_guide(synthetic_guide, tmp_path / "t.json", REF_TARGETS)
    )
    client = TestClient(create_app(runtime, None), base_url=BASE_URL)
    dataset_id = open_example(client)["id"]
    [quay] = client.get(
        f"/api/datasets/{dataset_id}/objects", params={"type": "Quay", "q": "SYN3"}
    ).json()["items"]
    window = client.get(f"/api/objects/{quay['id']}/xml").json()
    assert "\r" not in window["text"]
    utf16 = window["text"].encode("utf-16-le")
    marked = utf16[2 * window["focusFrom"] : 2 * window["focusTo"]].decode("utf-16-le")
    assert marked.startswith("<Quay") and marked.endswith("</Quay>")


def test_object_references_and_provenance(client: TestClient) -> None:
    data = open_example(client)
    quays = client.get(
        f"/api/datasets/{data['id']}/objects", params={"type": "Quay", "q": "SYN1"}
    ).json()["items"]
    quay = quays[0]
    detail = client.get(f"/api/objects/{quay['id']}").json()
    assert detail["reference"] is None
    assert detail["referencesTruncated"] is False
    assert detail["incoming"]
    first = detail["incoming"][0]
    assert first["element"]["name"] == "QuayRef"
    assert first["status"] == "resolved"
    assert first["target"]["id"] == quay["id"]
    assert first["owner"]["name"] == "PassengerStopAssignment"
    assert first["expected"] == ["Quay", "TaxiStand"]

    chain = client.get(f"/api/objects/{quay['id']}/provenance").json()
    assert [(link["kind"], link["object"]["name"]) for link in chain] == [
        ("frame", "SiteFrame"),
        ("object", "StopPlace"),
        ("object", "Quay"),
    ]
    assert chain[0]["object"]["colorKey"] == "SiteFrame"


def test_property_reference_and_reference_element(client: TestClient) -> None:
    data = open_example(client)
    assignments = client.get(
        f"/api/datasets/{data['id']}/objects", params={"type": "PassengerStopAssignment"}
    ).json()["items"]
    detail = client.get(f"/api/objects/{assignments[0]['id']}").json()
    refs = {p["name"]: p["reference"] for p in detail["properties"] if p["reference"]}
    assert set(refs) == {"ScheduledStopPointRef", "StopPlaceRef", "QuayRef"}
    assert refs["QuayRef"]["status"] == "resolved"
    assert refs["QuayRef"]["targetId"].startswith(data["id"] + ".")
    quay_ref = next(p for p in detail["properties"] if p["name"] == "QuayRef")
    own = client.get(f"/api/objects/{quay_ref['id']}").json()
    assert own["reference"]["ref"] == quay_ref["attributes"]["ref"]
    assert own["reference"]["target"]["name"] == "Quay"


def test_provenance_unknown_ids(client: TestClient) -> None:
    data = open_example(client)
    assert client.get(f"/api/objects/{data['id']}.99999999/provenance").status_code == 404
    assert client.get("/api/objects/ungueltig/provenance").status_code == 404


def test_reference_diagnostics_are_listed(client: TestClient) -> None:
    data = open_example(client, "ch20_midnight.xml")
    items = client.get(
        f"/api/datasets/{data['id']}/diagnostics", params={"category": "reference"}
    ).json()
    assert items == []
