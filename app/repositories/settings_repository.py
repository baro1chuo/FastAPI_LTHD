"""Tầng repository – bảng SYSTEM_SETTINGS (chỉ 1 dòng, id = 1, do seed.py tạo sẵn)."""
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.settings import SystemSettings


async def get(db: AsyncSession) -> SystemSettings:
    """Lấy dòng cài đặt duy nhất. Sửa cài đặt = đổi thuộc tính object này rồi service commit."""
    return await db.get(SystemSettings, 1)  # await: chờ SQLite trả dòng id = 1
