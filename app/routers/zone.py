from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_admin
from app.routers import not_implemented
from app.schemas.zone import ZoneCreate, ZoneOut, ZoneUpdate

router = APIRouter(prefix="/api/zones", tags=["Zones"])
# --- Guest (cong khai)  ---
@router.get("", response_model=list[ZoneOut])
def list_zones():

@router.get("/{zone_id}", response_model=ZoneOut)
def get_zone()

# --- Admin ---
@router.post("", response_model=ZoneOut, status_code=status.HTTP_201_CREATED)
def create_zone():

@router.put("/{zone_id}", response_model=ZoneOut)
def update_zone():

@router.delete("/{zone_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_zone():