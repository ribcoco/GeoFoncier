from __future__ import annotations

import json
from decimal import Decimal

from sqlalchemy import Numeric, func, select
from sqlalchemy.orm import Session

from app.core.exceptions import ParcelConflictError, ParcelNotFoundError
from app.repositories.parcel_repository import ParcelRepository
from app.schemas.parcel import ParcelCreate, ParcelResponse


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
            raise ParcelNotFoundError("La parcelle demandeee est introuvable.")

        return ParcelResponse.model_validate(response_payload)

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
