"""Tầng router – nhóm API NHÓM ĐỘNG VẬT (/api/categories). Chỉ đọc, công khai."""
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.schemas.category import CategoryOut
from app.services import category_service

router = APIRouter(prefix="/api/categories", tags=["Categories"])


@router.get("", response_model=list[CategoryOut])
async def list_categories(
    lang: str = Query("vi"),
    db: AsyncSession = Depends(get_db),
):
    """UC01 – danh sách nhóm động vật theo ngôn ngữ (dùng cho bộ lọc động vật theo nhóm)."""
    return await category_service.list_categories(db, lang)
