from decimal import Decimal

import pytest
from sqlalchemy import delete

from app.database.base import Base
from app.database.session import SessionLocal
from app.core.exceptions import ParcelConflictError
from app.models.parcel import Parcel
from app.schemas.parcel import ParcelCreate
from app.services.parcel_service import ParcelService


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
            delete(Parcel).where(Parcel.code_insee.like("9999%"))
        )


def test_service_creates_parcel_and_computes_surface() -> None:
    service = ParcelService()
    payload = ParcelCreate.model_validate(
        {
            "code_insee": "99999",
            "prefixe": "001",
            "section": "AA",
            "numero": "001",
            "geometry": valid_polygon(),
        }
    )

    with SessionLocal.begin() as session:
        result = service.create_parcel(session, payload)

    assert result.code_insee == "99999"
    assert result.geometry.type == "Polygon"
    assert result.bbox.type == "Polygon"
    assert result.surface_m2 > Decimal("0")


def test_service_rejects_duplicate_cadastral_reference() -> None:
    service = ParcelService()
    payload = ParcelCreate.model_validate(
        {
            "code_insee": "99998",
            "prefixe": "001",
            "section": "AA",
            "numero": "002",
            "geometry": valid_polygon(),
        }
    )

    with SessionLocal.begin() as session:
        service.create_parcel(session, payload)

    with SessionLocal.begin() as session:
        with pytest.raises(ParcelConflictError):
            service.create_parcel(session, payload)


def test_service_get_parcel_returns_created_parcel() -> None:
    service = ParcelService()
    payload = ParcelCreate.model_validate(
        {
            "code_insee": "99997",
            "prefixe": "001",
            "section": "AA",
            "numero": "003",
            "geometry": valid_polygon(),
        }
    )

    with SessionLocal.begin() as session:
        created = service.create_parcel(session, payload)

    with SessionLocal() as session:
        result = service.get_parcel(session, created.id)

    assert result.id == created.id
    assert result.numero == "003"
