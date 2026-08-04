# GeoFoncier

Minimal backend for cadastral parcel management with FastAPI, PostgreSQL, PostGIS, and Alembic.

## Quick Start

1. Copy `.env.example` to `.env` and adjust passwords if needed.
2. Start the stack:

```powershell
docker compose up --build -d
```

3. The API exposes `/health` and `/health/db`.

## Database and Import

Apply migrations:

```powershell
docker compose run --rm api alembic -c alembic.ini upgrade head
```

Import parcels from the CSV:

```powershell
docker compose run --rm api python -m app.scripts.import_parcels
```

The import is replay-safe and does not duplicate cadastral references.

## Tests

```powershell
docker compose run --rm api pytest tests/unit/test_health.py tests/unit/test_parcel_schemas.py tests/unit/test_import_parcels.py
docker compose run --rm api pytest tests/integration/test_health_db.py tests/integration/test_parcel_schema.py tests/integration/test_parcel_repository.py tests/integration/test_parcel_service.py
docker compose run --rm api ruff check app tests alembic
```

## Current Scope

- PostgreSQL/PostGIS stack
- Alembic migrations
- CSV import
- Parcel schema, repository, and service base
