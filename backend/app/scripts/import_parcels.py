from __future__ import annotations

import csv
import json
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from pathlib import Path

from sqlalchemy import select, text, tuple_

from app.database.session import SessionLocal
from app.models.parcel import Parcel

REQUIRED_COLUMNS = {
    "code_insee",
    "prefixe",
    "section",
    "numero",
    "geojson",
    "min_lon",
    "min_lat",
    "max_lon",
    "max_lat",
    "surface_m2",
}


@dataclass(slots=True)
class ImportSummary:
    imported: int = 0
    ignored: int = 0
    rejected: int = 0


def validate_columns(fieldnames: list[str] | None) -> None:
    if fieldnames is None:
        raise ValueError(
            "Le fichier CSV ne contient pas d'en-tete exploitable."
        )

    missing_columns = REQUIRED_COLUMNS.difference(fieldnames)
    if missing_columns:
        missing_columns_text = ", ".join(sorted(missing_columns))
        raise ValueError(
            f"Colonnes CSV manquantes: {missing_columns_text}."
        )


def parse_csv_row(row: dict[str, str]) -> dict[str, object]:
    try:
        geometry = json.loads(row["geojson"])
    except json.JSONDecodeError as exc:
        raise ValueError("Le GeoJSON de la ligne est invalide.") from exc

    if geometry.get("type") != "Polygon":
        raise ValueError("Le GeoJSON doit etre de type Polygon.")

    try:
        surface_m2 = Decimal(row["surface_m2"])
    except InvalidOperation as exc:
        raise ValueError("La surface CSV est invalide.") from exc

    return {
        "code_insee": row["code_insee"],
        "prefixe": row["prefixe"],
        "section": row["section"],
        "numero": row["numero"],
        "geojson": json.dumps(geometry),
        "surface_m2": surface_m2,
    }


def import_parcels(csv_path: Path, batch_size: int = 500) -> ImportSummary:
    summary = ImportSummary()
    insert_statement = text(
        """
        INSERT INTO parcels (
            code_insee,
            prefixe,
            section,
            numero,
            geometry,
            bbox,
            surface_m2
        )
        VALUES (
            :code_insee,
            :prefixe,
            :section,
            :numero,
            ST_SetSRID(ST_GeomFromGeoJSON(:geojson), 4326),
            ST_Envelope(ST_SetSRID(ST_GeomFromGeoJSON(:geojson), 4326)),
            :surface_m2
        )
        ON CONFLICT (
            code_insee,
            prefixe,
            section,
            numero
        ) DO NOTHING
        RETURNING id
        """
    )

    with csv_path.open("r", encoding="utf-8", newline="") as csv_file:
        reader = csv.DictReader(csv_file)
        validate_columns(reader.fieldnames)

        batch: list[dict[str, object]] = []

        for row in reader:
            try:
                parsed_row = parse_csv_row(row)
            except ValueError:
                summary.rejected += 1
                continue

            batch.append(parsed_row)
            if len(batch) == batch_size:
                _flush_batch(batch, insert_statement, summary)
                batch = []

        if batch:
            _flush_batch(batch, insert_statement, summary)

    return summary


def _flush_batch(
    batch: list[dict[str, object]],
    insert_statement: object,
    summary: ImportSummary,
) -> None:
    with SessionLocal.begin() as session:
        cadastral_references = [
            (
                row["code_insee"],
                row["prefixe"],
                row["section"],
                row["numero"],
            )
            for row in batch
        ]
        existing_references = {
            row
            for row in session.execute(
                select(
                    Parcel.code_insee,
                    Parcel.prefixe,
                    Parcel.section,
                    Parcel.numero,
                ).where(
                    tuple_(
                        Parcel.code_insee,
                        Parcel.prefixe,
                        Parcel.section,
                        Parcel.numero,
                    ).in_(cadastral_references)
                )
            )
        }
        session.execute(insert_statement, batch)
        inserted_count = len(batch) - len(existing_references)

    summary.imported += inserted_count
    summary.ignored += len(batch) - inserted_count


def main() -> None:
    csv_path = Path("/app/assets/parcelles.csv")
    summary = import_parcels(csv_path=csv_path)
    print(
        "Import termine - "
        f"imported={summary.imported} "
        f"ignored={summary.ignored} "
        f"rejected={summary.rejected}"
    )


if __name__ == "__main__":
    main()
