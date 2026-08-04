from sqlalchemy import text

from app.database.session import engine


def test_parcels_table_schema_matches_expected_shape() -> None:
    with engine.connect() as connection:
        table_name = connection.execute(
            text("SELECT to_regclass('public.parcels')")
        ).scalar_one()

        geometry_columns = connection.execute(
            text(
                """
                SELECT f_geometry_column, type, srid
                FROM geometry_columns
                WHERE f_table_schema = 'public'
                  AND f_table_name = 'parcels'
                ORDER BY f_geometry_column
                """
            )
        ).all()

        index_names = {
            row[0]
            for row in connection.execute(
                text(
                    """
                    SELECT indexname
                    FROM pg_indexes
                    WHERE schemaname = 'public'
                      AND tablename = 'parcels'
                    """
                )
            )
        }

        constraint_names = {
            row[0]
            for row in connection.execute(
                text(
                    """
                    SELECT conname
                    FROM pg_constraint
                    WHERE conrelid = 'public.parcels'::regclass
                    """
                )
            )
        }

    assert table_name == "parcels"
    assert geometry_columns == [
        ("bbox", "POLYGON", 4326),
        ("geometry", "POLYGON", 4326),
    ]
    assert "ix_parcels_bbox_gist" in index_names
    assert "ix_parcels_geometry_gist" in index_names
    assert "uq_parcels_cadastral_reference" in constraint_names
    assert "ck_parcels_geometry_valid" in constraint_names
    assert "ck_parcels_surface_positive" in constraint_names
