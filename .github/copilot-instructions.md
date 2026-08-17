# GeoFoncier — Copilot Instructions

## Language

- All code comments, docstrings, variable names, function names, and commit messages must be written in **English**.
- User-facing content (UI labels, error messages displayed to end users) must be in **French**.
- This file and configuration documentation may be written in French.

## Project Structure

```
GeoFoncier/
├── backend/          # API server (to be added)
├── frontend/         # Web application (to be added)
├── infra/
│   ├── db/
│   │   └── init-scripts/   # SQL scripts run on first DB startup (alphabetical order)
│   └── pgadmin/
│       └── servers.json    # pgAdmin pre-configured connection
├── docker-compose.yml
├── .env              # Local secrets — never commit
└── .env.example      # Template to commit
```

## Stack

- **Database**: PostgreSQL 16 + PostGIS 3.4 (`postgis/postgis:16-3.4`)
- **DB admin**: pgAdmin 4 (dev only, `localhost:5050`)
- **Orchestration**: Docker Compose

## Environment Variables

- Never hardcode credentials. Always use environment variables.
- All secrets go in `.env` (git-ignored). Use `.env.example` as the committed template.
- Required variables must use the `${VAR:?error message}` syntax in `docker-compose.yml` so the stack fails fast on missing config.

## Database

- All SQL migration/init scripts go in `infra/db/init-scripts/`.
- Name scripts with a numeric prefix for ordering: `01_`, `02_`, etc.
- Always use `IF NOT EXISTS` / `IF EXISTS` guards in SQL scripts to make them idempotent.
- Spatial columns must use SRID **2154** (RGF93 / Lambert-93) for metropolitan France unless otherwise specified.
- Prefer `geometry` over `geography` for local French data.

## Docker

- Volume names follow the pattern `geofoncier_<service>`.

## Security

- Never commit `.env` files or any file containing secrets.
- Follow OWASP Top 10 guidelines.
- Validate all inputs at system boundaries.
