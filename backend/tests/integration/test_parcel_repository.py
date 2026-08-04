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
