"""Tầng repository – bảng SYSTEM_SETTINGS (chỉ 1 dòng, id = 1, do seed.py tạo sẵn)."""
from sqlalchemy.orm import Session

from app.models.settings import SystemSettings


def get(db: Session) -> SystemSettings:
    """Lấy dòng cài đặt duy nhất. Sửa cài đặt = đổi thuộc tính object này rồi service commit."""
    return db.get(SystemSettings, 1)
