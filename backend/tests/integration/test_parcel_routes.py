from fastapi.testclient import TestClient
import pytest
from sqlalchemy import func, select
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


def polygon_at(
    lon: float,
    lat: float,
    delta: float = 0.01,
) -> dict[str, object]:
    return {
        "type": "Polygon",
        "coordinates": [
            [
                [lon, lat],
                [lon + delta, lat],
                [lon + delta, lat + delta],
                [lon, lat],
            ]
        ],
    }


@pytest.fixture(autouse=True)
def cleanup_test_parcels() -> None:
    Base.metadata.create_all(bind=SessionLocal.kw["bind"])
    with SessionLocal() as session:
        baseline_max_id = session.execute(
            select(func.max(Parcel.id))
        ).scalar_one_or_none()

    yield

    min_new_id = (baseline_max_id or 0) + 1
    with SessionLocal.begin() as session:
        session.execute(
            delete(Parcel).where(Parcel.id >= min_new_id)
        )


def test_post_parcel_returns_201() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/parcels",
        json={
            "code_insee": "TST70",
            "prefixe": "001",
            "section": "AA",
            "numero": "001",
            "geometry": valid_polygon(),
        },
    )

    assert response.status_code == 201
    body = response.json()
    assert body["code_insee"] == "TST70"
    assert body["geometry"]["type"] == "Polygon"
    assert Decimal(body["surface_m2"]) > Decimal("0")


def test_get_parcel_returns_200() -> None:
    client = TestClient(app)
    create_response = client.post(
        "/api/parcels",
        json={
            "code_insee": "TST71",
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
        "code_insee": "TST72",
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
            "code_insee": "TST73",
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


def test_post_parcel_returns_422_when_geometry_is_invalid() -> None:
    client = TestClient(app)
    response = client.post(
        "/api/parcels",
        json={
            "code_insee": "TST74",
            "prefixe": "001",
            "section": "AA",
            "numero": "018",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [0.0, 0.0],
                        [2.0, 0.0],
                        [0.0, 2.0],
                        [2.0, 2.0],
                        [0.0, 0.0],
                    ]
                ],
            },
        },
    )

    assert response.status_code == 422
    assert response.json()["detail"]["code"] == "PARCEL_INVALID"


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
            "code_insee": "TST74",
            "prefixe": "001",
            "section": "AA",
            "numero": "005",
            "geometry": valid_polygon(),
        },
    )
    second = client.post(
        "/api/parcels",
        json={
            "code_insee": "TST75",
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


def test_delete_parcel_returns_204_and_removes_resource() -> None:
    client = TestClient(app)
    create_response = client.post(
        "/api/parcels",
        json={
            "code_insee": "TST76",
            "prefixe": "001",
            "section": "AA",
            "numero": "007",
            "geometry": valid_polygon(),
        },
    )
    created_id = create_response.json()["id"]

    delete_response = client.delete(f"/api/parcels/{created_id}")
    get_response = client.get(f"/api/parcels/{created_id}")

    assert delete_response.status_code == 204
    assert get_response.status_code == 404
    assert get_response.json()["detail"]["code"] == "PARCEL_NOT_FOUND"


def test_delete_parcel_returns_404_when_missing() -> None:
    client = TestClient(app)

    response = client.delete("/api/parcels/99999999")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "PARCEL_NOT_FOUND"


def test_search_parcels_returns_intersecting_results() -> None:
    client = TestClient(app)
    first = client.post(
        "/api/parcels",
        json={
            "code_insee": "TST77",
            "prefixe": "001",
            "section": "AA",
            "numero": "008",
            "geometry": polygon_at(1.40, 43.60),
        },
    )
    client.post(
        "/api/parcels",
        json={
            "code_insee": "TST78",
            "prefixe": "001",
            "section": "AA",
            "numero": "009",
            "geometry": polygon_at(2.40, 44.60),
        },
    )

    response = client.post(
        "/api/parcels/search",
        json={
            "geometry": polygon_at(1.405, 43.605, 0.005),
            "limit": 100,
            "offset": 0,
        },
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == first.json()["id"]


def test_search_parcels_returns_empty_list_when_no_intersection() -> None:
    client = TestClient(app)
    client.post(
        "/api/parcels",
        json={
            "code_insee": "TST79",
            "prefixe": "001",
            "section": "AA",
            "numero": "010",
            "geometry": polygon_at(1.40, 43.60),
        },
    )

    response = client.post(
        "/api/parcels/search",
        json={
            "geometry": polygon_at(5.00, 48.00),
            "limit": 100,
            "offset": 0,
        },
    )

    assert response.status_code == 200
    assert response.json() == []


def test_get_parcel_neighbors_returns_touching_parcels() -> None:
    client = TestClient(app)
    center = client.post(
        "/api/parcels",
        json={
            "code_insee": "TST80",
            "prefixe": "001",
            "section": "AA",
            "numero": "011",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [1.00, 43.00],
                        [1.01, 43.00],
                        [1.01, 43.01],
                        [1.00, 43.00],
                    ]
                ],
            },
        },
    )
    east_neighbor = client.post(
        "/api/parcels",
        json={
            "code_insee": "TST81",
            "prefixe": "001",
            "section": "AA",
            "numero": "012",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [1.01, 43.00],
                        [1.02, 43.00],
                        [1.02, 43.01],
                        [1.01, 43.00],
                    ]
                ],
            },
        },
    )
    client.post(
        "/api/parcels",
        json={
            "code_insee": "TST82",
            "prefixe": "001",
            "section": "AA",
            "numero": "013",
            "geometry": polygon_at(2.00, 45.00),
        },
    )

    response = client.get(f"/api/parcels/{center.json()['id']}/neighbors")

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    assert body[0]["id"] == east_neighbor.json()["id"]


def test_get_parcel_neighbors_supports_pagination() -> None:
    client = TestClient(app)
    center = client.post(
        "/api/parcels",
        json={
            "code_insee": "TST83",
            "prefixe": "001",
            "section": "AA",
            "numero": "014",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [1.10, 43.10],
                        [1.11, 43.10],
                        [1.11, 43.11],
                        [1.10, 43.10],
                    ]
                ],
            },
        },
    )
    west_neighbor = client.post(
        "/api/parcels",
        json={
            "code_insee": "TST84",
            "prefixe": "001",
            "section": "AA",
            "numero": "015",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [1.09, 43.10],
                        [1.10, 43.10],
                        [1.10, 43.11],
                        [1.09, 43.10],
                    ]
                ],
            },
        },
    )
    east_neighbor = client.post(
        "/api/parcels",
        json={
            "code_insee": "TST85",
            "prefixe": "001",
            "section": "AA",
            "numero": "016",
            "geometry": {
                "type": "Polygon",
                "coordinates": [
                    [
                        [1.11, 43.10],
                        [1.12, 43.10],
                        [1.12, 43.11],
                        [1.11, 43.10],
                    ]
                ],
            },
        },
    )

    response = client.get(
        f"/api/parcels/{center.json()['id']}/neighbors?limit=1&offset=1"
    )

    assert response.status_code == 200
    body = response.json()
    assert len(body) == 1
    returned_id = body[0]["id"]
    neighbor_ids = [
        west_neighbor.json()["id"],
        east_neighbor.json()["id"],
    ]
    assert returned_id in neighbor_ids


def test_get_parcel_neighbors_returns_404_when_missing() -> None:
    client = TestClient(app)

    response = client.get("/api/parcels/99999999/neighbors")

    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "PARCEL_NOT_FOUND"
