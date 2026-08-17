from __future__ import annotations

import json
from decimal import Decimal

from sqlalchemy import Numeric, func, select
from sqlalchemy.orm import Session

from app.core.exceptions import ParcelConflictError, ParcelNotFoundError
from app.repositories.parcel_repository import ParcelRepository
from app.schemas.parcel import (
    ParcelCreate,
    ParcelResponse,
    ParcelSearchRequest,
    ParcelUpdate,
)


class ParcelService:
    def __init__(self, repository: ParcelRepository | None = None) -> None:
        self.repository = repository or ParcelRepository()

    def create_parcel(
        self,
        session: Session,
        payload: ParcelCreate,
    ) -> ParcelResponse:
        existing = self.repository.get_by_cadastral_reference(
            session,
            code_insee=payload.code_insee,
            prefixe=payload.prefixe,
            section=payload.section,
            numero=payload.numero,
        )
        if existing is not None:
            raise ParcelConflictError(
                "Une parcelle existe deja pour cette reference cadastrale."
            )

        surface_m2 = self._compute_surface_m2(
            session,
            payload.geometry.model_dump(),
        )
        parcel = self.repository.create(
            session,
            code_insee=payload.code_insee,
            prefixe=payload.prefixe,
            section=payload.section,
            numero=payload.numero,
            geometry_geojson=payload.geometry.model_dump(),
            surface_m2=surface_m2,
        )

        response_payload = self.repository.get_geojson_by_id(
            session,
            parcel.id,
        )
        if response_payload is None:
            raise ParcelNotFoundError(
                "La parcelle creee est introuvable en base."
            )

        return ParcelResponse.model_validate(response_payload)

    def get_parcel(self, session: Session, parcel_id: int) -> ParcelResponse:
        response_payload = self.repository.get_geojson_by_id(
            session,
            parcel_id,
        )
        if response_payload is None:
            raise ParcelNotFoundError("La parcelle demandee est introuvable.")

        return ParcelResponse.model_validate(response_payload)

    def update_parcel(
        self,
        session: Session,
        parcel_id: int,
        payload: ParcelUpdate,
    ) -> ParcelResponse:
        parcel = self.repository.get_by_id(session, parcel_id)
        if parcel is None:
            raise ParcelNotFoundError("La parcelle demandee est introuvable.")

        patch_data = payload.model_dump(
            exclude_unset=True,
            exclude_none=True,
        )

        target_code_insee = patch_data.get("code_insee", parcel.code_insee)
        target_prefixe = patch_data.get("prefixe", parcel.prefixe)
        target_section = patch_data.get("section", parcel.section)
        target_numero = patch_data.get("numero", parcel.numero)

        existing = self.repository.get_by_cadastral_reference(
            session,
            code_insee=target_code_insee,
            prefixe=target_prefixe,
            section=target_section,
            numero=target_numero,
        )
        if existing is not None and existing.id != parcel.id:
            raise ParcelConflictError(
                "Une parcelle existe deja pour cette reference cadastrale."
            )

        geometry_geojson = patch_data.get("geometry")
        surface_m2: Decimal | None = None
        if geometry_geojson is not None:
            surface_m2 = self._compute_surface_m2(session, geometry_geojson)

        updated = self.repository.update(
            session,
            parcel=parcel,
            code_insee=patch_data.get("code_insee"),
            prefixe=patch_data.get("prefixe"),
            section=patch_data.get("section"),
            numero=patch_data.get("numero"),
            geometry_geojson=geometry_geojson,
            surface_m2=surface_m2,
        )

        response_payload = self.repository.get_geojson_by_id(
            session,
            updated.id,
        )
        if response_payload is None:
            raise ParcelNotFoundError(
                "La parcelle mise a jour est introuvable en base."
            )

        return ParcelResponse.model_validate(response_payload)

    def delete_parcel(self, session: Session, parcel_id: int) -> None:
        parcel = self.repository.get_by_id(session, parcel_id)
        if parcel is None:
            raise ParcelNotFoundError("La parcelle demandee est introuvable.")

        self.repository.delete(session, parcel)

    def search_parcels(
        self,
        session: Session,
        payload: ParcelSearchRequest,
    ) -> list[ParcelResponse]:
        results = self.repository.search_geojson_by_intersection(
            session,
            geometry_geojson=payload.geometry.model_dump(),
            limit=payload.limit,
            offset=payload.offset,
        )
        return [
            ParcelResponse.model_validate(result)
            for result in results
        ]

    def get_parcel_neighbors(
        self,
        session: Session,
        parcel_id: int,
        *,
        limit: int,
        offset: int,
    ) -> list[ParcelResponse]:
        parcel = self.repository.get_by_id(session, parcel_id)
        if parcel is None:
            raise ParcelNotFoundError("La parcelle demandee est introuvable.")

        results = self.repository.get_neighbors_geojson_by_id(
            session,
            parcel_id=parcel_id,
            limit=limit,
            offset=offset,
        )
        return [
            ParcelResponse.model_validate(result)
            for result in results
        ]

    def _compute_surface_m2(
        self,
        session: Session,
        geometry_geojson: dict[str, object],
    ) -> Decimal:
        geometry_text = json.dumps(geometry_geojson)
        geometry = func.ST_SetSRID(
            func.ST_GeomFromGeoJSON(geometry_text),
            4326,
        )
        statement = select(
            func.round(
                func.cast(
                    func.ST_Area(
                        func.ST_Transform(geometry, 2154)
                    ),
                    Numeric,
                ),
                2,
            )
        )
        surface_m2 = session.execute(statement).scalar_one()
        return Decimal(surface_m2)
