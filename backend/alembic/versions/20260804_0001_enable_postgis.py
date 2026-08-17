"""Enable PostGIS extension.

Revision ID: 20260804_0001
Revises:
Create Date: 2026-08-04 00:00:00
"""

from typing import Sequence

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "20260804_0001"
down_revision: str | None = None
branch_labels: Sequence[str] | None = None
depends_on: Sequence[str] | None = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS postgis")


def downgrade() -> None:
    op.execute("DROP EXTENSION IF EXISTS postgis_tiger_geocoder")
    op.execute("DROP EXTENSION IF EXISTS postgis_topology")
    op.execute("DROP EXTENSION IF EXISTS postgis")