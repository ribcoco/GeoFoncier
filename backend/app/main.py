from fastapi import Depends, FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.core.config import get_settings

settings = get_settings()

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
)


@app.get("/health", tags=["health"])
def healthcheck() -> dict[str, str]:
    return {"message": "API operationnelle"}


@app.get("/health/db", tags=["health"])
def healthcheck_database(db: Session = Depends(get_db)) -> dict[str, str]:
    try:
        db.execute(text("SELECT PostGIS_Full_Version()"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503,
            detail={
                "code": "DATABASE_UNAVAILABLE",
                "message": "La base de donnees est indisponible.",
            },
        ) from exc

    return {"message": "Connexion base de donnees operationnelle"}