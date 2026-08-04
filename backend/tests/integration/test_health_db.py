from fastapi.testclient import TestClient

from app.main import app


def test_database_healthcheck_returns_200() -> None:
    client = TestClient(app)

    response = client.get("/health/db")

    assert response.status_code == 200
    expected_message = (
        "Connexion base de donnees "
        "operationnelle"
    )
    assert response.json() == {"message": expected_message}