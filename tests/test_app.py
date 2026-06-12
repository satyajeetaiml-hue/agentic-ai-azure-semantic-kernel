"""Tests for the Semantic Kernel claims validator (runs the real kernel + plugin)."""

from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_mock():
    r = client.get("/health")
    assert r.status_code == 200
    assert r.json()["framework"] == "semantic-kernel"
    assert r.json()["mode"] == "mock"


def test_active_policy_approved():
    r = client.post("/api/v1/claims/validate", json={"claim_text": "Accident, policy POL-12345, bumper."})
    assert r.status_code == 200
    body = r.json()
    assert body["policy_number"] == "POL-12345"
    assert body["valid"] is True
    assert "collision" in body["coverage"]
    assert body["decision"] == "approved"
    assert body["invoked_via"] == "semantic-kernel native plugin"


def test_lapsed_policy_rejected():
    r = client.post("/api/v1/claims/validate", json={"claim_text": "Water damage, policy POL-00001."})
    body = r.json()
    assert body["status"] == "lapsed"
    assert body["decision"] == "rejected"


def test_unknown_policy_needs_review():
    r = client.post("/api/v1/claims/validate", json={"claim_text": "Claim under policy POL-99999."})
    body = r.json()
    assert body["status"] == "not_found"
    assert body["decision"] == "needs_review"


def test_no_policy_needs_review():
    r = client.post("/api/v1/claims/validate", json={"claim_text": "I had an accident."})
    assert r.json()["decision"] == "needs_review"


def test_validation_rejects_empty():
    assert client.post("/api/v1/claims/validate", json={"claim_text": ""}).status_code == 422
