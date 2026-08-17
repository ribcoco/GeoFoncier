from decimal import Decimal
from pathlib import Path

import pytest

from app.scripts.import_parcels import (
    REQUIRED_COLUMNS,
    ImportSummary,
    import_parcels,
    parse_csv_row,
    validate_columns,
)


def test_validate_columns_accepts_expected_header() -> None:
    validate_columns(list(REQUIRED_COLUMNS))


def test_validate_columns_rejects_missing_columns() -> None:
    with pytest.raises(ValueError):
        validate_columns(["code_insee", "prefixe"])


def test_parse_csv_row_accepts_valid_polygon() -> None:
    row = {
        "code_insee": "31555",
        "prefixe": "806",
        "section": "AB",
        "numero": "139",
        "geojson": (
            '{"type":"Polygon","coordinates":'
            '[[[1.0,43.0],[1.1,43.0],[1.1,43.1],[1.0,43.0]]]}'
        ),
        "min_lon": "1.0",
        "min_lat": "43.0",
        "max_lon": "1.1",
        "max_lat": "43.1",
        "surface_m2": "123.45",
    }

    parsed = parse_csv_row(row)

    assert parsed["code_insee"] == "31555"
    assert parsed["surface_m2"] == Decimal("123.45")


def test_parse_csv_row_rejects_invalid_geojson() -> None:
    row = {
        "code_insee": "31555",
        "prefixe": "806",
        "section": "AB",
        "numero": "139",
        "geojson": "not-json",
        "min_lon": "1.0",
        "min_lat": "43.0",
        "max_lon": "1.1",
        "max_lat": "43.1",
        "surface_m2": "123.45",
    }

    with pytest.raises(ValueError):
        parse_csv_row(row)


def test_import_parcels_rejects_missing_header(tmp_path: Path) -> None:
    csv_path = tmp_path / "invalid.csv"
    csv_path.write_text("code_insee,prefixe\n31555,806\n", encoding="utf-8")

    with pytest.raises(ValueError):
        import_parcels(csv_path)


def test_import_summary_defaults_to_zero() -> None:
    summary = ImportSummary()

    assert summary.imported == 0
    assert summary.ignored == 0
    assert summary.rejected == 0
