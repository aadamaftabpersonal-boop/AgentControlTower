import json
from pathlib import Path

from fastapi.testclient import TestClient

from app import entire_client
from app.main import app

client = TestClient(app)

FIXTURES = Path(__file__).parent / "fixtures"


def _load_fixture(name: str) -> list[dict]:
    return json.loads((FIXTURES / name).read_text())


def test_health_still_ok():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "repo_root" in body


def test_version_still_unchanged():
    response = client.get("/version")
    assert response.status_code == 200
    assert response.json() == {"version": "0.1.0"}


def test_checkpoints_returns_json_object_not_bare_array(monkeypatch):
    fixture = _load_fixture("pending_live.json")
    monkeypatch.setattr(entire_client, "list_pending_checkpoints", lambda **_: fixture)

    response = client.get("/api/checkpoints")

    assert response.status_code == 200
    body = response.json()
    assert isinstance(body, dict)
    assert body["status"] == "OK"
    assert "checkpoints" in body
    assert "notes" in body
    assert len(body["checkpoints"]) == 1


def test_checkpoints_normalizes_live_pending_entry(monkeypatch):
    fixture = _load_fixture("pending_live.json")
    monkeypatch.setattr(entire_client, "list_pending_checkpoints", lambda **_: fixture)

    response = client.get("/api/checkpoints")

    cp = response.json()["checkpoints"][0]
    assert cp["checkpoint_id"] == fixture[0]["id"]
    assert cp["prompt"] == fixture[0]["session_prompt"]
    assert cp["detail_level"] == "list_only"
    assert cp["evidence_status"] == "OK"
    assert cp["condensation_id"] is None
    assert cp["unavailable_fields"] == ["transcript", "tool_calls", "commits"]


def test_checkpoints_returns_waiting_for_agent_activity_when_empty(monkeypatch):
    monkeypatch.setattr(entire_client, "list_pending_checkpoints", lambda **_: [])

    response = client.get("/api/checkpoints")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "WAITING FOR AGENT ACTIVITY"
    assert body["checkpoints"] == []
