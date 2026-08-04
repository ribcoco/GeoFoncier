import pytest
from pydantic import ValidationError

from app.schemas.parcel import (
    GeoJSONPolygon,
    ParcelCreate,
    ParcelSearchRequest,
    ParcelUpdate,
)


def valid_polygon() -> dict[str, object]:
    return {
        "type": "Polygon",
        "coordinates": [
            [
                [1.0, 43.0],
                [1.1, 43.0],
                [1.1, 43.1],
                [1.0, 43.0],
            ]
        ],
    }


def test_geojson_polygon_accepts_valid_polygon() -> None:
    polygon = GeoJSONPolygon.model_validate(valid_polygon())

    assert polygon.type == "Polygon"
    assert polygon.coordinates[0][0] == [1.0, 43.0]


def test_geojson_polygon_rejects_wrong_type() -> None:
    payload = valid_polygon() | {"type": "MultiPolygon"}

    with pytest.raises(ValidationError):
        GeoJSONPolygon.model_validate(payload)


def test_geojson_polygon_rejects_empty_coordinates() -> None:
    payload = {"type": "Polygon", "coordinates": []}

    with pytest.raises(ValidationError):
        GeoJSONPolygon.model_validate(payload)


def test_geojson_polygon_rejects_open_ring() -> None:
    payload = {
        "type": "Polygon",
        "coordinates": [
            [
                [1.0, 43.0],
                [1.1, 43.0],
                [1.1, 43.1],
                [1.0, 43.1],
            ]
        ],
    }

    with pytest.raises(ValidationError):
        GeoJSONPolygon.model_validate(payload)


def test_geojson_polygon_rejects_invalid_longitude() -> None:
    payload = {
        "type": "Polygon",
        "coordinates": [
            [
                [190.0, 43.0],
                [1.1, 43.0],
                [1.1, 43.1],
                [190.0, 43.0],
            ]
        ],
    }

    with pytest.raises(ValidationError):
        GeoJSONPolygon.model_validate(payload)


def test_parcel_create_accepts_valid_payload() -> None:
    payload = {
        "code_insee": "31555",
        "prefixe": "806",
        "section": "AB",
        "numero": "139",
        "geometry": valid_polygon(),
    }

    parcel = ParcelCreate.model_validate(payload)

    assert parcel.code_insee == "31555"


def test_parcel_update_rejects_empty_payload() -> None:
    with pytest.raises(ValidationError):
        ParcelUpdate.model_validate({})


def test_search_request_applies_default_pagination() -> None:
    request = ParcelSearchRequest.model_validate({"geometry": valid_polygon()})

    assert request.limit == 100
    assert request.offset == 0
