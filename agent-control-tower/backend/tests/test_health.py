from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_ok():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["status"] == "ok"
    assert "repo_root" in body


def test_version():
    response = client.get("/version")
    assert response.status_code == 200
    body = response.json()
    assert body["version"] == "0.1.0"
