"""Truy vấn bảng SYSTEM_SETTINGS (chỉ 1 dòng, id = 1)."""
from sqlalchemy.orm import Session

from app.models.settings import SystemSettings


def get(db: Session) -> SystemSettings:
    """Lấy dòng cài đặt duy nhất (init_db luôn tạo sẵn)."""
    return db.get(SystemSettings, 1)
