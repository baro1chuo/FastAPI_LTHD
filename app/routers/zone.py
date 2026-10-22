"""Tầng router – nhóm API KHU VỰC (/api/zones). Chỉ đọc, công khai; đã bỏ API thêm/sửa/xóa khu vực."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.zone import ZoneOut
from app.services import zone_service

router = APIRouter(prefix="/api/zones", tags=["Zones"])


@router.get("", response_model=list[ZoneOut])
def list_zones(
    lang: str = Query("vi"),
    db: Session = Depends(get_db),
):
    """UC01 – danh sách khu vực theo ngôn ngữ (dùng cho bộ lọc động vật theo khu vực)."""
    return zone_service.list_zones(db, lang)
