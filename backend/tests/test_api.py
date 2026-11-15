"""Integration tests for the Flask API layer (validation + error handling)."""
import pytest

from app import app as flask_app


@pytest.fixture
def client():
    flask_app.config["TESTING"] = True
    return flask_app.test_client()


def test_health(client):
    resp = client.get("/api/health")
    assert resp.status_code == 200
    assert resp.get_json()["status"] == "ok"


def test_climate_default(client):
    resp = client.get("/api/climate")
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["summary"]["period"] == "2016-2025"
    assert "imerg_image_count" not in body["summary"]["statistics"]
    assert "imerg_image_count" in body["summary"]["excluded_columns"]


def test_climate_invalid_months(client):
    resp = client.get("/api/climate?months=13,abc")
    assert resp.status_code == 400


def test_assess_malformed_date_returns_400(client):
    resp = client.post("/api/assess", json={"wheat_harvest_date": "not-a-date"})
    assert resp.status_code == 400
    assert "wheat_harvest_date" in resp.get_json()["error"]


def test_assess_invalid_irrigation_source_returns_400(client):
    resp = client.post("/api/assess", json={"irrigation_source": "well-of-wishes"})
    assert resp.status_code == 400


def test_assess_non_json_body_returns_400(client):
    resp = client.post("/api/assess", data="not json", content_type="text/plain")
    assert resp.status_code == 400


def test_assess_full_valid_payload(client):
    resp = client.post("/api/assess", json={
        "wheat_sow_date": "2025-11-15",
        "wheat_harvest_date": "2026-04-20",
        "rice_transplant_date": "2026-07-05",
        "irrigation_source": "tubewell",
        "irrigation_available": "available",
    })
    assert resp.status_code == 200
    body = resp.get_json()
    assert body["baseline"]["result"] == "Suitable within calendar constraints"
    assert body["alternative"]["result"] != "Suitable within calendar constraints"
    for scenario in ("baseline", "alternative"):
        for field in ("result", "validation_status", "reasons", "constraints_and_risks",
                      "supporting_data", "evidence_confidence", "limitations"):
            assert field in body[scenario]
