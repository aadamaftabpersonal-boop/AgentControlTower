import json
from pathlib import Path

from fastapi.testclient import TestClient

from app import entire_client
from app.main import app

client = TestClient(app)

FIXTURES = Path(__file__).parent / "fixtures"


def _load_fixture(name: str) -> list[dict]:
    return json.loads((FIXTURES / name).read_text())


def test_checkpoint_detail_returns_404_for_unknown_id(monkeypatch):
    monkeypatch.setattr(entire_client, "list_pending_checkpoints", lambda **_: [])
    response = client.get("/api/checkpoints/does-not-exist")
    assert response.status_code == 404


def test_checkpoint_detail_returns_matching_checkpoint(monkeypatch):
    fixture = _load_fixture("pending_live.json")
    monkeypatch.setattr(entire_client, "list_pending_checkpoints", lambda **_: fixture)

    response = client.get(f"/api/checkpoints/{fixture[0]['id']}")

    assert response.status_code == 200
    assert response.json()["checkpoint_id"] == fixture[0]["id"]


def test_reconstruction_prompt_returns_unverified_prompt(monkeypatch):
    fixture = _load_fixture("pending_live.json")
    monkeypatch.setattr(entire_client, "list_pending_checkpoints", lambda **_: fixture)

    response = client.get(f"/api/checkpoints/{fixture[0]['id']}/reconstruction-prompt")

    assert response.status_code == 200
    body = response.json()
    assert body["verification_status"] == "UNVERIFIED"
    assert body["checkpoint_id"] == fixture[0]["id"]
    assert len(body["prompt"]) > 0


def test_reconstruction_prompt_404s_for_unknown_id(monkeypatch):
    monkeypatch.setattr(entire_client, "list_pending_checkpoints", lambda **_: [])
    response = client.get("/api/checkpoints/does-not-exist/reconstruction-prompt")
    assert response.status_code == 404
