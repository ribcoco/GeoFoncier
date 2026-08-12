from decimal import Decimal

import pytest
from sqlalchemy import func, select
from sqlalchemy import delete

from app.core.exceptions import ParcelConflictError, ParcelNotFoundError
from app.database.base import Base
from app.database.session import SessionLocal
from app.models.parcel import Parcel
from app.schemas.parcel import ParcelCreate, ParcelSearchRequest
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


def test_service_creates_parcel_and_computes_surface() -> None:
    service = ParcelService()
    payload = ParcelCreate.model_validate(
        {
            "code_insee": "TSV99",
            "prefixe": "001",
            "section": "AA",
            "numero": "001",
            "geometry": valid_polygon(),
        }
    )

    with SessionLocal.begin() as session:
        result = service.create_parcel(session, payload)

    assert result.code_insee == "TSV99"
    assert result.geometry.type == "Polygon"
    assert result.bbox.type == "Polygon"
    assert result.surface_m2 > Decimal("0")


def test_service_rejects_duplicate_cadastral_reference() -> None:
    service = ParcelService()
    payload = ParcelCreate.model_validate(
        {
            "code_insee": "TSV98",
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
            "code_insee": "TSV97",
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


def test_service_search_parcels_returns_intersections() -> None:
    service = ParcelService()

    with SessionLocal.begin() as session:
        service.create_parcel(
            session,
            ParcelCreate.model_validate(
                {
                    "code_insee": "TSV96",
                    "prefixe": "001",
                    "section": "AA",
                    "numero": "011",
                    "geometry": polygon_at(1.40, 43.60),
                }
            ),
        )
        service.create_parcel(
            session,
            ParcelCreate.model_validate(
                {
                    "code_insee": "TSV95",
                    "prefixe": "001",
                    "section": "AA",
                    "numero": "012",
                    "geometry": polygon_at(2.40, 44.60),
                }
            ),
        )

    with SessionLocal() as session:
        result = service.search_parcels(
            session,
            ParcelSearchRequest.model_validate(
                {
                    "geometry": polygon_at(1.405, 43.605, 0.005),
                    "limit": 100,
                    "offset": 0,
                }
            ),
        )

    assert len(result) == 1
    assert result[0].code_insee == "TSV96"


def test_service_get_neighbors_returns_touching_parcels() -> None:
    service = ParcelService()
    with SessionLocal.begin() as session:
        center = service.create_parcel(
            session,
            ParcelCreate.model_validate(
                {
                    "code_insee": "TSV94",
                    "prefixe": "001",
                    "section": "AA",
                    "numero": "013",
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
                }
            ),
        )
        service.create_parcel(
            session,
            ParcelCreate.model_validate(
                {
                    "code_insee": "TSV93",
                    "prefixe": "001",
                    "section": "AA",
                    "numero": "014",
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
                }
            ),
        )

    with SessionLocal() as session:
        neighbors = service.get_parcel_neighbors(
            session,
            center.id,
            limit=100,
            offset=0,
        )

    assert len(neighbors) == 1
    assert neighbors[0].code_insee == "TSV93"


def test_service_get_neighbors_raises_not_found() -> None:
    service = ParcelService()

    with SessionLocal() as session:
        with pytest.raises(ParcelNotFoundError):
            service.get_parcel_neighbors(
                session,
                99999999,
                limit=100,
                offset=0,
            )
