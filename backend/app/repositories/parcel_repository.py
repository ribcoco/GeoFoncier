import json
from decimal import Decimal
from typing import Any

from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.parcel import Parcel
from app.schemas.parcel import geojson_polygon_from_mapping


class ParcelRepository:
    def _build_geojson_response_payload(self, row: Any) -> dict[str, Any]:
        geometry = geojson_polygon_from_mapping(json.loads(row[8]))
        bbox = geojson_polygon_from_mapping(json.loads(row[9]))

        return {
            "id": row[0],
            "code_insee": row[1],
            "prefixe": row[2],
            "section": row[3],
            "numero": row[4],
            "surface_m2": row[5],
            "created_at": row[6],
            "updated_at": row[7],
            "geometry": geometry,
            "bbox": bbox,
        }

    def create(
        self,
        session: Session,
        *,
        code_insee: str,
        prefixe: str,
        section: str,
        numero: str,
        geometry_geojson: dict[str, Any],
        surface_m2: Decimal,
    ) -> Parcel:
        geometry_text = json.dumps(geometry_geojson)
        geometry = func.ST_SetSRID(
            func.ST_GeomFromGeoJSON(geometry_text),
            4326,
        )

        parcel = Parcel(
            code_insee=code_insee,
            prefixe=prefixe,
            section=section,
            numero=numero,
            geometry=geometry,
            bbox=func.ST_Envelope(geometry),
            surface_m2=surface_m2,
        )
        session.add(parcel)
        session.flush()
        session.refresh(parcel)
        return parcel

    def get_by_id(self, session: Session, parcel_id: int) -> Parcel | None:
        return session.get(Parcel, parcel_id)

    def get_by_cadastral_reference(
        self,
        session: Session,
        *,
        code_insee: str,
        prefixe: str,
        section: str,
        numero: str,
    ) -> Parcel | None:
        statement = select(Parcel).where(
            Parcel.code_insee == code_insee,
            Parcel.prefixe == prefixe,
            Parcel.section == section,
            Parcel.numero == numero,
        )
        return session.execute(statement).scalar_one_or_none()

    def update(
        self,
        session: Session,
        *,
        parcel: Parcel,
        code_insee: str | None = None,
        prefixe: str | None = None,
        section: str | None = None,
        numero: str | None = None,
        geometry_geojson: dict[str, Any] | None = None,
        surface_m2: Decimal | None = None,
    ) -> Parcel:
        if code_insee is not None:
            parcel.code_insee = code_insee
        if prefixe is not None:
            parcel.prefixe = prefixe
        if section is not None:
            parcel.section = section
        if numero is not None:
            parcel.numero = numero

        if geometry_geojson is not None:
            geometry_text = json.dumps(geometry_geojson)
            geometry = func.ST_SetSRID(
                func.ST_GeomFromGeoJSON(geometry_text),
                4326,
            )
            parcel.geometry = geometry
            parcel.bbox = func.ST_Envelope(geometry)
            if surface_m2 is not None:
                parcel.surface_m2 = surface_m2

        session.add(parcel)
        session.flush()
        session.refresh(parcel)
        return parcel

    def delete(self, session: Session, parcel: Parcel) -> None:
        session.delete(parcel)
        session.flush()

    def get_geojson_by_id(
        self,
        session: Session,
        parcel_id: int,
    ) -> dict[str, Any] | None:
        statement = select(
            Parcel.id,
            Parcel.code_insee,
            Parcel.prefixe,
            Parcel.section,
            Parcel.numero,
            Parcel.surface_m2,
            Parcel.created_at,
            Parcel.updated_at,
            func.ST_AsGeoJSON(Parcel.geometry),
            func.ST_AsGeoJSON(Parcel.bbox),
        ).where(Parcel.id == parcel_id)

        row = session.execute(statement).one_or_none()
        if row is None:
            return None

        return self._build_geojson_response_payload(row)

    def search_geojson_by_intersection(
        self,
        session: Session,
        *,
        geometry_geojson: dict[str, Any],
        limit: int,
        offset: int,
    ) -> list[dict[str, Any]]:
        geometry_text = json.dumps(geometry_geojson)
        search_geometry = func.ST_SetSRID(
            func.ST_GeomFromGeoJSON(geometry_text),
            4326,
        )

        statement = (
            select(
                Parcel.id,
                Parcel.code_insee,
                Parcel.prefixe,
                Parcel.section,
                Parcel.numero,
                Parcel.surface_m2,
                Parcel.created_at,
                Parcel.updated_at,
                func.ST_AsGeoJSON(Parcel.geometry),
                func.ST_AsGeoJSON(Parcel.bbox),
            )
            .where(func.ST_Intersects(Parcel.geometry, search_geometry))
            .order_by(Parcel.id)
            .limit(limit)
            .offset(offset)
        )

        rows = session.execute(statement).all()
        return [
            self._build_geojson_response_payload(row)
            for row in rows
        ]
