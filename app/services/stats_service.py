"""Tầng service – UC15 Xem thống kê. Chỉ đọc, không thay đổi dữ liệu (quy tắc UC15)."""
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.animal import Animal
from app.models.user import User
from app.models.zone import Zone
from app.repositories import stats_repository


async def get_dashboard(db: AsyncSession) -> dict:
    """UC15 – số liệu tổng quan: tổng động vật (gồm cả đang ẩn), khu vực, người dùng, đánh giá theo trạng thái.

    Các câu đếm chạy TUẦN TỰ (await từng câu): không dùng asyncio.gather vì một AsyncSession
    không chạy song song nhiều câu truy vấn được.
    Trả về: dict theo schema DashboardOut. CSDL trống thì mọi số là 0 (UC15 E1). Không ném lỗi.
    """
    by_status = await stats_repository.count_reviews_by_status(db)
    return {
        "total_animals": await stats_repository.count_all(db, Animal),
        "total_zones": await stats_repository.count_all(db, Zone),
        "total_users": await stats_repository.count_all(db, User),
        "total_reviews": sum(by_status.values()),
        "reviews_by_status": by_status,  # trạng thái không có đánh giá nào -> schema điền 0
    }
