from fastapi.testclient import TestClient

from app.main import app


def test_healthcheck_returns_200() -> None:
    client = TestClient(app)

    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"message": "API operationnelle"}
