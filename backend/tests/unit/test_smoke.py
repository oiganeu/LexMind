"""Backend smoke tests."""

from fastapi.testclient import TestClient

from lexmind.main import app


def test_app_importable() -> None:
    assert app is not None


def test_health_endpoint() -> None:
    client = TestClient(app)
    response = client.get("/")
    assert response.status_code == 200
    body = response.json()
    assert body["name"] == "LexMind"
    assert body["status"] == "ok"
    assert body["version"]
