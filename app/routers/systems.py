"""Tầng router – nhóm API SYSTEMS (/api/systems): thống kê (UC15) và cài đặt hệ thống (UC16). Chỉ Admin.

Mọi endpoint là async def vì đều chờ truy vấn SQLite.
"""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.deps import require_admin
from app.schemas.systems import DashboardOut, SettingsOut, SettingsUpdate
from app.services import settings_service, stats_service

router = APIRouter(
    prefix="/api/systems",
    tags=["Systems"],
    dependencies=[Depends(require_admin)],  # mọi API trong nhóm đều yêu cầu Admin (401/403)
)


@router.get("/dashboard", response_model=DashboardOut)
async def dashboard(db: AsyncSession = Depends(get_db)):
    """UC15 – thống kê: tổng động vật, khu vực, người dùng, số đánh giá theo trạng thái."""
    return await stats_service.get_dashboard(db)


@router.get("/settings", response_model=SettingsOut)
async def get_settings(db: AsyncSession = Depends(get_db)):
    """UC16 – xem cài đặt hệ thống hiện tại."""
    return await settings_service.get_settings(db)


@router.put("/settings", response_model=SettingsOut)
async def update_settings(data: SettingsUpdate, db: AsyncSession = Depends(get_db)):
    """UC16 – cập nhật cài đặt (chỉ field được gửi). 400 ngôn ngữ không hỗ trợ, 422 sai định dạng."""
    return await settings_service.update_settings(db, data)
