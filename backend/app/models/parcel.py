from datetime import datetime
from decimal import Decimal

from geoalchemy2 import Geometry
from geoalchemy2.elements import WKBElement
from sqlalchemy import (
    CheckConstraint,
    DateTime,
    Numeric,
    String,
    UniqueConstraint,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class Parcel(Base):
    __tablename__ = "parcels"

    __table_args__ = (
        UniqueConstraint(
            "code_insee",
            "prefixe",
            "section",
            "numero",
            name="uq_parcels_cadastral_reference",
        ),
        CheckConstraint(
            "ST_IsValid(geometry)",
            name="ck_parcels_geometry_valid",
        ),
        CheckConstraint("surface_m2 > 0", name="ck_parcels_surface_positive"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    code_insee: Mapped[str] = mapped_column(String(5), nullable=False)
    prefixe: Mapped[str] = mapped_column(String(10), nullable=False)
    section: Mapped[str] = mapped_column(String(10), nullable=False)
    numero: Mapped[str] = mapped_column(String(10), nullable=False)
    geometry: Mapped[WKBElement] = mapped_column(
        Geometry(geometry_type="POLYGON", srid=4326, spatial_index=True),
        nullable=False,
    )
    bbox: Mapped[WKBElement] = mapped_column(
        Geometry(geometry_type="POLYGON", srid=4326, spatial_index=True),
        nullable=False,
    )
    surface_m2: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        server_default=func.now(),
        onupdate=func.now(),
    )
