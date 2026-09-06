import json
from pathlib import Path

from fastapi.testclient import TestClient

from app import entire_client
from app.main import app

client = TestClient(app)

FIXTURES = Path(__file__).parent / "fixtures"


def _load_fixture(name: str) -> list[dict]:
    return json.loads((FIXTURES / name).read_text())


def test_agents_returns_one_agent_for_one_live_checkpoint(monkeypatch):
    fixture = _load_fixture("pending_live.json")
    monkeypatch.setattr(entire_client, "list_pending_checkpoints", lambda: fixture)

    response = client.get("/api/agents")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "OK"
    assert len(body["agents"]) == 1
    assert body["agents"][0]["session_id"] == fixture[0]["session_id"]


def test_agents_reports_waiting_for_agent_activity_with_no_checkpoints(monkeypatch):
    monkeypatch.setattr(entire_client, "list_pending_checkpoints", lambda: [])

    response = client.get("/api/agents")

    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "WAITING FOR AGENT ACTIVITY"
    assert body["agents"] == []


def test_cors_headers_present_for_vite_dev_origin(monkeypatch):
    monkeypatch.setattr(entire_client, "list_pending_checkpoints", lambda: [])

    response = client.get("/api/agents", headers={"Origin": "http://localhost:5174"})

    assert response.headers.get("access-control-allow-origin") == "http://localhost:5174"
