from fastapi.testclient import TestClient
import pytest
from sqlalchemy import delete
from decimal import Decimal

from app.database.base import Base
from app.database.session import SessionLocal
from app.main import app
from app.models.parcel import Parcel


def valid_polygon() -> dict[str, object]:
    return {
        "type": "Polygon",
        "coordinates": [
            [
                [1.45, 43.61],
                [1.46, 43.61],
                [1.46, 43.62],
                [1.45, 43.61],
            ]
        ],
    }


@pytest.fixture(autouse=True)
def cleanup_test_parcels() -> None:
    Base.metadata.create_all(bind=SessionLocal.kw["bind"])
    with SessionLocal.begin() as session:
        session.execute(
            delete(Parcel).where(Parcel.code_insee.like("9997%"))
        )


def test_post_parcel_returns_201() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/parcels",
        json={
            "code_insee": "99970",
            "prefixe": "001",
            "section": "AA",
            "numero": "001",
            "geometry": valid_polygon(),
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["code_insee"] == "99970"
    assert body["geometry"]["type"] == "Polygon"
    assert Decimal(body["surface_m2"]) > Decimal("0")


def test_get_parcel_returns_200() -> None:
    client = TestClient(app)
    create_response = client.post(
        "/api/parcels",
        json={
            "code_insee": "99971",
            "prefixe": "001",
            "section": "AA",
            "numero": "002",
            "geometry": valid_polygon(),
        },
    )
    created_id = create_response.json()["id"]

    response = client.get(f"/api/parcels/{created_id}")

    assert response.status_code == 200
    assert response.json()["id"] == created_id


def test_get_parcel_returns_404_when_missing() -> None:
    client = TestClient(app)
    response = client.get("/api/parcels/99999999")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "PARCEL_NOT_FOUND"


def test_post_parcel_returns_409_on_duplicate_reference() -> None:
    client = TestClient(app)
    payload = {
        "code_insee": "99972",
        "prefixe": "001",
        "section": "AA",
        "numero": "003",
        "geometry": valid_polygon(),
    }

    first_response = client.post("/api/parcels", json=payload)
    second_response = client.post("/api/parcels", json=payload)

    assert first_response.status_code == 201
    assert second_response.status_code == 409
    assert second_response.json()["detail"]["code"] == "PARCEL_CONFLICT"


def test_patch_parcel_returns_200() -> None:
    client = TestClient(app)
    create_response = client.post(
        "/api/parcels",
        json={
            "code_insee": "99973",
            "prefixe": "001",
            "section": "AA",
            "numero": "004",
            "geometry": valid_polygon(),
        },
    )
    created = create_response.json()

    response = client.patch(
        f"/api/parcels/{created['id']}",
        json={
            "numero": "099",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [1.45, 43.61],
                        [1.47, 43.61],
                        [1.47, 43.63],
                        [1.45, 43.61],
                    ]
                ],
            },
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert body["id"] == created["id"]
    assert body["numero"] == "099"
    assert Decimal(body["surface_m2"]) > Decimal("0")


def test_patch_parcel_returns_404_when_missing() -> None:
    client = TestClient(app)
    response = client.patch(
        "/api/parcels/99999999",
        json={"numero": "100"},
    )

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "PARCEL_NOT_FOUND"


def test_patch_parcel_returns_409_on_duplicate_reference() -> None:
    client = TestClient(app)
    first = client.post(
        "/api/parcels",
        json={
            "code_insee": "99974",
            "prefixe": "001",
            "section": "AA",
            "numero": "005",
            "geometry": valid_polygon(),
        },
    )
    second = client.post(
        "/api/parcels",
        json={
            "code_insee": "99975",
            "prefixe": "001",
            "section": "AA",
            "numero": "006",
            "geometry": valid_polygon(),
        },
    )

    response = client.patch(
        f"/api/parcels/{second.json()['id']}",
        json={
            "code_insee": first.json()["code_insee"],
            "prefixe": first.json()["prefixe"],
            "section": first.json()["section"],
            "numero": first.json()["numero"],
        },
    )

    assert response.status_code == 409
    assert response.json()["detail"]["code"] == "PARCEL_CONFLICT"
