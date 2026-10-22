"""Tầng router – nhóm API NHÓM ĐỘNG VẬT (/api/categories). Chỉ đọc, công khai."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.schemas.category import CategoryOut
from app.services import category_service

router = APIRouter(prefix="/api/categories", tags=["Categories"])


@router.get("", response_model=list[CategoryOut])
def list_categories(
    lang: str = Query("vi"),
    db: Session = Depends(get_db),
):
    """UC01 – danh sách nhóm động vật theo ngôn ngữ (dùng cho bộ lọc động vật theo nhóm)."""
    return category_service.list_categories(db, lang)
