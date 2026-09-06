"""Regression coverage: a specified repo target is never silently swapped
for the backend's own default, and the response always names exactly which
resolved path it read from.
"""

from fastapi.testclient import TestClient

from app import entire_client
from app.config import settings
from app.main import app

client = TestClient(app)


def test_agents_uses_the_given_repo_not_the_default(tmp_path, monkeypatch):
    other_repo = tmp_path / "other-repo"
    (other_repo / ".git").mkdir(parents=True)

    captured_roots = []

    def fake_list(**kwargs):
        captured_roots.append(kwargs.get("repo_root"))
        return []

    monkeypatch.setattr(entire_client, "list_pending_checkpoints", fake_list)

    response = client.get("/api/agents", params={"repo": str(other_repo)})

    assert response.status_code == 200
    assert len(captured_roots) == 1
    # The exact resolved path was used -- never settings.repo_root (the
    # backend's own default), and never silently substituted on any branch.
    assert captured_roots[0] == other_repo.resolve()
    assert captured_roots[0] != settings.repo_root


def test_agents_response_names_the_resolved_repo_root(tmp_path, monkeypatch):
    other_repo = tmp_path / "other-repo"
    (other_repo / ".git").mkdir(parents=True)
    monkeypatch.setattr(entire_client, "list_pending_checkpoints", lambda **_: [])

    response = client.get("/api/agents", params={"repo": str(other_repo)})

    assert response.json()["repo_root"] == str(other_repo.resolve())


def test_invalid_repo_target_never_falls_back_to_default(monkeypatch):
    calls = []
    monkeypatch.setattr(entire_client, "list_pending_checkpoints", lambda **_: calls.append(1) or [])

    response = client.get("/api/agents", params={"repo": "/definitely/does/not/exist"})

    assert response.status_code == 400
    # The invalid target must never fall through to a real ingestion call
    # against the default repo -- a 400 means nothing was read at all.
    assert calls == []


def test_checkpoints_response_repo_root_matches_default_when_no_repo_given(monkeypatch):
    monkeypatch.setattr(entire_client, "list_pending_checkpoints", lambda **_: [])

    response = client.get("/api/checkpoints")

    assert response.json()["repo_root"] == str(settings.repo_root)
