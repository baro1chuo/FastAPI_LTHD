from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_admin
from app.routers import not_implemented
from app.schemas.zone import ZoneCreate, ZoneOut, ZoneUpdate

router = APIRouter(prefix="/api/zones", tags=["Zones"])

# --- Guest ---
@router.get("", response_model=list[ZoneOut])
def list_zones(
    q: str | None = Query(None, description="Tìm theo tên khu vực"),
    lang: str = Query("vi"),
    db: Session = Depends(get_db),
):
    not_implemented("zone_service.list_zones")


@router.get("/{zone_id}", response_model=ZoneOut)
def get_zone(
    zone_id: int,
    lang: str = Query("vi"),
    db: Session = Depends(get_db),
):
    not_implemented("zone_service.get_zone")


# --- Admin ---
@router.post("", response_model=ZoneOut, status_code=status.HTTP_201_CREATED)
def create_zone(
    data: ZoneCreate,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    not_implemented("zone_service.create_zone")


@router.put("/{zone_id}", response_model=ZoneOut)
def update_zone(
    zone_id: int,
    data: ZoneUpdate,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    not_implemented("zone_service.update_zone")


@router.delete("/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_zone(
    zone_id: int,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    # TODO: zone_service.delete_zone -> 409 nếu khu vực còn động vật
    not_implemented("zone_service.delete_zone")
    return Response(status_code=status.HTTP_204_NO_CONTENT)