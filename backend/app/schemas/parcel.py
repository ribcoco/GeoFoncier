from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import (
    BaseModel,
    ConfigDict,
    Field,
    field_validator,
    model_validator,
)


def _validate_position(position: list[float]) -> list[float]:
    if len(position) != 2:
        raise ValueError(
            "Chaque coordonnee doit contenir une longitude et une latitude."
        )

    longitude, latitude = position
    if not -180 <= longitude <= 180:
        raise ValueError("La longitude doit etre comprise entre -180 et 180.")
    if not -90 <= latitude <= 90:
        raise ValueError("La latitude doit etre comprise entre -90 et 90.")

    return position


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    detail: ErrorDetail


class GeoJSONPolygon(BaseModel):
    model_config = ConfigDict(extra="forbid")

    type: str
    coordinates: list[list[list[float]]]

    @field_validator("type")
    @classmethod
    def validate_type(cls, value: str) -> str:
        if value != "Polygon":
            raise ValueError("La geometrie doit etre de type Polygon.")
        return value

    @field_validator("coordinates")
    @classmethod
    def validate_coordinates(
        cls,
        coordinates: list[list[list[float]]],
    ) -> list[list[list[float]]]:
        if not coordinates:
            raise ValueError(
                "Le polygon GeoJSON doit contenir au moins un anneau."
            )

        for ring in coordinates:
            if len(ring) < 4:
                raise ValueError(
                    "Chaque anneau doit contenir au moins quatre positions."
                )
            validated_ring = [
                _validate_position(position)
                for position in ring
            ]
            if validated_ring[0] != validated_ring[-1]:
                raise ValueError("Chaque anneau doit etre ferme.")

        return coordinates


class ParcelBase(BaseModel):
    code_insee: str = Field(min_length=5, max_length=5)
    prefixe: str = Field(min_length=1, max_length=10)
    section: str = Field(min_length=1, max_length=10)
    numero: str = Field(min_length=1, max_length=10)


class ParcelCreate(ParcelBase):
    geometry: GeoJSONPolygon


class ParcelUpdate(BaseModel):
    code_insee: str | None = Field(default=None, min_length=5, max_length=5)
    prefixe: str | None = Field(default=None, min_length=1, max_length=10)
    section: str | None = Field(default=None, min_length=1, max_length=10)
    numero: str | None = Field(default=None, min_length=1, max_length=10)
    geometry: GeoJSONPolygon | None = None

    @model_validator(mode="after")
    def validate_not_empty(self) -> "ParcelUpdate":
        if not any(
            [
                self.code_insee,
                self.prefixe,
                self.section,
                self.numero,
                self.geometry,
            ]
        ):
            raise ValueError(
                "La requete de mise a jour ne peut pas etre vide."
            )
        return self


class ParcelSearchRequest(BaseModel):
    geometry: GeoJSONPolygon
    limit: int = Field(default=100, ge=1, le=500)
    offset: int = Field(default=0, ge=0)


class ParcelResponse(ParcelBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    surface_m2: Decimal
    geometry: GeoJSONPolygon
    bbox: GeoJSONPolygon
    created_at: datetime
    updated_at: datetime


def geojson_polygon_from_mapping(mapping: dict[str, Any]) -> GeoJSONPolygon:
    return GeoJSONPolygon.model_validate(mapping)
