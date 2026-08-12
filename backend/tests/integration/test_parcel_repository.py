from decimal import Decimal

import pytest
from sqlalchemy import delete

from app.database.base import Base
from app.database.session import SessionLocal
from app.models.parcel import Parcel
from app.repositories.parcel_repository import ParcelRepository


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
def prepare_parcels_table() -> None:
    Base.metadata.create_all(bind=SessionLocal.kw["bind"])
    with SessionLocal.begin() as session:
        session.execute(delete(Parcel))


def test_repository_creates_and_reads_parcel_with_geojson() -> None:
    repository = ParcelRepository()

    with SessionLocal.begin() as session:
        created = repository.create(
            session,
            code_insee="31555",
            prefixe="806",
            section="AB",
            numero="139",
            geometry_geojson=valid_polygon(),
            surface_m2=Decimal("123.45"),
        )
        created_id = created.id

    with SessionLocal() as session:
        parcel = repository.get_by_id(session, created_id)
        assert parcel is not None
        assert parcel.code_insee == "31555"
        assert parcel.surface_m2 == Decimal("123.45")

        payload = repository.get_geojson_by_id(session, created_id)
        assert payload is not None
        assert payload["code_insee"] == "31555"
        assert payload["geometry"].type == "Polygon"
        assert payload["bbox"].type == "Polygon"


def test_repository_get_by_cadastral_reference_returns_matching_parcel(
) -> None:
    repository = ParcelRepository()

    with SessionLocal.begin() as session:
        repository.create(
            session,
            code_insee="31555",
            prefixe="806",
            section="AD",
            numero="679",
            geometry_geojson=valid_polygon(),
            surface_m2=Decimal("456.78"),
        )

    with SessionLocal() as session:
        parcel = repository.get_by_cadastral_reference(
            session,
            code_insee="31555",
            prefixe="806",
            section="AD",
            numero="679",
        )

        assert parcel is not None
        assert parcel.numero == "679"


def test_repository_search_geojson_by_intersection_returns_matches() -> None:
    repository = ParcelRepository()

    with SessionLocal.begin() as session:
        repository.create(
            session,
            code_insee="31556",
            prefixe="001",
            section="AA",
            numero="001",
            geometry_geojson=polygon_at(1.40, 43.60),
            surface_m2=Decimal("100.00"),
        )
        repository.create(
            session,
            code_insee="31557",
            prefixe="001",
            section="AA",
            numero="002",
            geometry_geojson=polygon_at(2.40, 44.60),
            surface_m2=Decimal("100.00"),
        )

    with SessionLocal() as session:
        results = repository.search_geojson_by_intersection(
            session,
            geometry_geojson=polygon_at(1.405, 43.605, 0.005),
            limit=100,
            offset=0,
        )

    assert len(results) == 1
    assert results[0]["code_insee"] == "31556"


def test_repository_get_neighbors_geojson_by_id_returns_touching() -> None:
    repository = ParcelRepository()

    with SessionLocal.begin() as session:
        center = repository.create(
            session,
            code_insee="31558",
            prefixe="001",
            section="AA",
            numero="003",
            geometry_geojson={
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
            surface_m2=Decimal("100.00"),
        )
        repository.create(
            session,
            code_insee="31559",
            prefixe="001",
            section="AA",
            numero="004",
            geometry_geojson={
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
            surface_m2=Decimal("100.00"),
        )

    with SessionLocal() as session:
        results = repository.get_neighbors_geojson_by_id(
            session,
            parcel_id=center.id,
            limit=100,
            offset=0,
        )

    assert len(results) == 1
    assert results[0]["code_insee"] == "31559"
