"""Truy vấn bảng ZONE, ZONE_TRANSLATION. Hiện mới có hàm animal_service cần; phần khu vực (UC12) bổ sung sau."""
from sqlalchemy.orm import Session

from app.models.zone import Zone


def exists(db: Session, zone_id: int) -> bool:
    """Khu vực có tồn tại không."""
    return db.get(Zone, zone_id) is not None
