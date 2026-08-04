from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.api.dependencies import get_db
from app.schemas.parcel import ErrorResponse, ParcelCreate, ParcelResponse
from app.services.parcel_service import ParcelService

router = APIRouter(prefix="/api/parcels", tags=["parcels"])
service = ParcelService()


@router.post(
    "",
    response_model=ParcelResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        409: {
            "model": ErrorResponse,
        },
        422: {
            "model": ErrorResponse,
        },
    },
)
def create_parcel(
    payload: ParcelCreate,
    db: Session = Depends(get_db),
) -> ParcelResponse:
    result = service.create_parcel(db, payload)
    db.commit()
    return result


@router.get(
    "/{parcel_id}",
    response_model=ParcelResponse,
    status_code=status.HTTP_200_OK,
    responses={
        404: {
            "model": ErrorResponse,
        }
    },
)
def get_parcel(
    parcel_id: int,
    db: Session = Depends(get_db),
) -> ParcelResponse:
    return service.get_parcel(db, parcel_id)
