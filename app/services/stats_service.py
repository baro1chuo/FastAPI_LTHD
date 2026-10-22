"""Tầng service – UC15 Xem thống kê. Chỉ đọc, không thay đổi dữ liệu (quy tắc UC15)."""
from sqlalchemy.orm import Session

from app.models.animal import Animal
from app.models.user import User
from app.models.zone import Zone
from app.repositories import stats_repository


def get_dashboard(db: Session) -> dict:
    """UC15 – số liệu tổng quan: tổng động vật (gồm cả đang ẩn), khu vực, người dùng, đánh giá theo trạng thái.

    Trả về: dict theo schema DashboardOut. CSDL trống thì mọi số là 0 (UC15 E1). Không ném lỗi.
    """
    by_status = stats_repository.count_reviews_by_status(db)
    return {
        "total_animals": stats_repository.count_all(db, Animal),
        "total_zones": stats_repository.count_all(db, Zone),
        "total_users": stats_repository.count_all(db, User),
        "total_reviews": sum(by_status.values()),
        "reviews_by_status": by_status,  # trạng thái không có đánh giá nào -> schema điền 0
    }
