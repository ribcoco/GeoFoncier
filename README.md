# GeoFoncier

Minimal backend for cadastral parcel management with FastAPI, PostgreSQL, PostGIS, and Alembic.

## Quick Start

1. Copy `.env.example` to `.env` and adjust passwords if needed.
2. Start the stack:

```powershell
docker compose up --build -d
```

3. The API exposes `/health`, `/health/db`, `POST /api/parcels`, `GET /api/parcels/{parcel_id}`, `PATCH /api/parcels/{parcel_id}`, `DELETE /api/parcels/{parcel_id}`, `POST /api/parcels/search`, and `GET /api/parcels/{parcel_id}/neighbors`.

## First Launch

Use this sequence for a clean first run:

1. Create your local environment file.

```powershell
cp .env.example .env
```

2. Start containers.

```powershell
docker compose up --build -d
```

3. Apply database migrations.

```powershell
docker compose run --rm api alembic -c alembic.ini upgrade head
```

4. Import CSV data.

```powershell
docker compose run --rm api python -m app.scripts.import_parcels
```

5. Verify API and DB health.

```powershell
curl http://localhost:8000/health
curl http://localhost:8000/health/db
```

Expected result: both endpoints return `200 OK`.

## API Usage

Base URL:

```text
http://localhost:8000
```

Example polygon used below:

```json
{
	"type": "Polygon",
	"coordinates": [
		[
			[1.45, 43.61],
			[1.46, 43.61],
			[1.46, 43.62],
			[1.45, 43.61]
		]
	]
}
```

### 1) `GET /health`

Purpose: basic API liveness check.

```bash
curl http://localhost:8000/health
```

Expected: `200 OK`.

### 2) `GET /health/db`

Purpose: database connectivity check.

```bash
curl http://localhost:8000/health/db
```

Expected: `200 OK`.

### 3) `POST /api/parcels`

Purpose: create a parcel.

```bash
curl -X POST http://localhost:8000/api/parcels \
	-H "Content-Type: application/json" \
	-d '{
		"code_insee": "31555",
		"prefixe": "001",
		"section": "AA",
		"numero": "123",
		"geometry": {
			"type": "Polygon",
			"coordinates": [[[1.45,43.61],[1.46,43.61],[1.46,43.62],[1.45,43.61]]]
		}
	}'
```

Expected:
- `201 Created` on success.
- `409` if cadastral reference already exists.
- `422` if payload is invalid.

### 4) `GET /api/parcels/{parcel_id}`

Purpose: get one parcel by id.

```bash
curl http://localhost:8000/api/parcels/1
```

Expected:
- `200 OK` with parcel payload.
- `404` if not found.

### 5) `PATCH /api/parcels/{parcel_id}`

Purpose: partially update a parcel.

```bash
curl -X PATCH http://localhost:8000/api/parcels/1 \
	-H "Content-Type: application/json" \
	-d '{
		"numero": "124",
		"geometry": {
			"type": "Polygon",
			"coordinates": [[[1.45,43.61],[1.47,43.61],[1.47,43.63],[1.45,43.61]]]
		}
	}'
```

Expected:
- `200 OK` on success.
- `404` if parcel does not exist.
- `409` if updated cadastral reference conflicts with another parcel.
- `422` if payload is invalid or empty.

### 6) `DELETE /api/parcels/{parcel_id}`

Purpose: delete one parcel.

```bash
curl -X DELETE http://localhost:8000/api/parcels/1
```

Expected:
- `204 No Content` on success.
- `404` if parcel does not exist.

### 7) `POST /api/parcels/search`

Purpose: find parcels intersecting an input polygon.

```bash
curl -X POST http://localhost:8000/api/parcels/search \
	-H "Content-Type: application/json" \
	-d '{
		"geometry": {
			"type": "Polygon",
			"coordinates": [[[1.45,43.61],[1.47,43.61],[1.47,43.63],[1.45,43.61]]]
		},
		"limit": 100,
		"offset": 0
	}'
```

Expected:
- `200 OK` with a list (possibly empty).
- `422` if payload is invalid.

### 8) `GET /api/parcels/{parcel_id}/neighbors`

Purpose: list touching neighbor parcels for a given parcel id.

```bash
curl "http://localhost:8000/api/parcels/1/neighbors?limit=100&offset=0"
```

Expected:
- `200 OK` with a list (possibly empty).
- `404` if target parcel does not exist.
- `422` if pagination parameters are invalid.

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
docker compose run --rm api pytest tests/integration/test_parcel_routes.py
docker compose run --rm api ruff check app tests alembic
```

## Current Scope

- PostgreSQL/PostGIS stack
- Alembic migrations
- CSV import
- Parcel schema, repository, and service base
- Parcel API routes: create, read, update, delete, search, neighbors
