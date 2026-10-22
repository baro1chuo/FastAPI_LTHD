"""Tầng repository – các câu đếm cho trang thống kê (UC15), async. Chỉ đọc, không ghi CSDL."""
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.base import Base
from app.models.review import Review


async def count_all(db: AsyncSession, model: type[Base]) -> int:
    """Đếm số dòng của một bảng (vd count_all(db, Animal)). Dùng COUNT(*) trong SQL, không tải dữ liệu về."""
    return await db.scalar(select(func.count()).select_from(model))  # await: chờ SQLite đếm


async def count_reviews_by_status(db: AsyncSession) -> dict[str, int]:
    """Số đánh giá theo từng trạng thái, vd {"pending": 3, "approved": 8}; trạng thái không có thì không xuất hiện.

    Dùng GROUP BY để CSDL đếm 1 lần cho mọi trạng thái thay vì 3 câu truy vấn.
    """
    rows = (await db.execute(select(Review.status, func.count()).group_by(Review.status))).all()
    return {status: count for status, count in rows}
