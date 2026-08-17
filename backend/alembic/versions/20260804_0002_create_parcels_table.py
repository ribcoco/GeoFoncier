"""Create parcels table.

Revision ID: 20260804_0002
Revises: 20260804_0001
Create Date: 2026-08-04 00:30:00
"""

from typing import Sequence

from alembic import op
from geoalchemy2 import Geometry
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "20260804_0002"
down_revision: str | None = "20260804_0001"
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.create_table(
        "parcels",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("code_insee", sa.String(length=5), nullable=False),
        sa.Column("prefixe", sa.String(length=10), nullable=False),
        sa.Column("section", sa.String(length=10), nullable=False),
        sa.Column("numero", sa.String(length=10), nullable=False),
        sa.Column(
            "geometry",
            Geometry(geometry_type="POLYGON", srid=4326, spatial_index=False),
            nullable=False,
        ),
        sa.Column(
            "bbox",
            Geometry(geometry_type="POLYGON", srid=4326, spatial_index=False),
            nullable=False,
        ),
        sa.Column("surface_m2", sa.Numeric(12, 2), nullable=False),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.Column(
            "updated_at",
            sa.DateTime(timezone=True),
            nullable=False,
            server_default=sa.text("CURRENT_TIMESTAMP"),
        ),
        sa.UniqueConstraint(
            "code_insee",
            "prefixe",
            "section",
            "numero",
            name="uq_parcels_cadastral_reference",
        ),
        sa.CheckConstraint(
            "ST_IsValid(geometry)",
            name="ck_parcels_geometry_valid",
        ),
        sa.CheckConstraint(
            "surface_m2 > 0",
            name="ck_parcels_surface_positive",
        ),
    )
    op.create_index(
        "ix_parcels_geometry_gist",
        "parcels",
        ["geometry"],
        unique=False,
        postgresql_using="gist",
    )
    op.create_index(
        "ix_parcels_bbox_gist",
        "parcels",
        ["bbox"],
        unique=False,
        postgresql_using="gist",
    )


def downgrade() -> None:
    op.drop_index(
        "ix_parcels_bbox_gist",
        table_name="parcels",
        postgresql_using="gist",
    )
    op.drop_index(
        "ix_parcels_geometry_gist",
        table_name="parcels",
        postgresql_using="gist",
    )
    op.drop_table("parcels")
