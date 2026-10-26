"""Tầng repository – truy vấn bảng REVIEW, async (nối USER để lấy tên người viết, ANIMAL_TRANSLATION để lấy tên động vật).

Chỉ viết câu truy vấn; không kiểm tra quy tắc nghiệp vụ, không commit.
"""
from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.animal import Animal, AnimalTranslation
from app.models.review import Review
from app.models.user import User

# Một dòng kết quả danh sách: (đánh giá, họ tên người viết, tên động vật theo ngôn ngữ)
ReviewRow = tuple[Review, str, str]


async def get_by_id(db: AsyncSession, review_id: int) -> Review | None:
    """Lấy đánh giá theo id; không có -> None."""
    return await db.get(Review, review_id)


async def get_by_user_and_animal(db: AsyncSession, user_id: int, animal_id: int) -> Review | None:
    """Đánh giá của user cho động vật này (UNIQUE(animalId, userId)); chưa có -> None."""
    return await db.scalar(select(Review).where(Review.user_id == user_id, Review.animal_id == animal_id))


def _apply_filters(stmt: Select, animal_id: int | None, user_id: int | None, statuses: list[str] | None,
                   user_name: str | None, visible_only: bool) -> Select:
    """Thêm điều kiện lọc vào câu SELECT (đã JOIN user và animal); bộ lọc nào None/False thì bỏ qua."""
    if animal_id is not None:
        stmt = stmt.where(Review.animal_id == animal_id)
    if user_id is not None:
        stmt = stmt.where(Review.user_id == user_id)
    if statuses:
        stmt = stmt.where(Review.status.in_(statuses))
    if user_name:
        stmt = stmt.where(User.full_name.ilike(f"%{user_name}%"))  # tìm gần đúng theo tên người viết
    if visible_only:
        stmt = stmt.where(Animal.available.is_(True))  # khách không thấy đánh giá của động vật đang ẩn
    return stmt


def _select_with_names(lang: str, default_lang: str) -> Select:
    """SELECT đánh giá kèm họ tên người viết và tên động vật (theo lang, thiếu thì ngôn ngữ mặc định,
    thiếu nữa thì tên khoa học)."""
    tr = aliased(AnimalTranslation)
    tr_def = aliased(AnimalTranslation)
    animal_name = func.coalesce(tr.name, tr_def.name, Animal.scientific_name)
    return (
        select(Review, User.full_name, animal_name)
        .join(User, User.id == Review.user_id)        # JOIN thường: đánh giá luôn có người viết
        .join(Animal, Animal.id == Review.animal_id)  # và luôn có động vật (khóa ngoại NOT NULL)
        # LEFT JOIN bản dịch: động vật thiếu bản dịch vẫn ra được đánh giá
        .outerjoin(tr, (tr.animal_id == Animal.id) & (tr.lang == lang))
        .outerjoin(tr_def, (tr_def.animal_id == Animal.id) & (tr_def.lang == default_lang))
    )


async def list_reviews(db: AsyncSession, lang: str, default_lang: str, animal_id: int | None = None,
                 user_id: int | None = None, statuses: list[str] | None = None,
                 user_name: str | None = None, visible_only: bool = False,
                 offset: int = 0, limit: int = 20) -> list[ReviewRow]:
    """Danh sách đánh giá kèm tên người viết + tên động vật, mới nhất trước, có phân trang.

    Tham số lọc: animal_id, user_id, statuses (vd ['approved']), user_name (gần đúng),
    visible_only (chỉ động vật đang hiển thị). Trả về: list các bộ (Review, user_name, animal_name).
    """
    stmt = _apply_filters(_select_with_names(lang, default_lang),
                          animal_id, user_id, statuses, user_name, visible_only)
    stmt = stmt.order_by(Review.created_at.desc(), Review.id.desc()).offset(offset).limit(limit)
    return [tuple(row) for row in (await db.execute(stmt)).all()]  # await: chờ SQLite trả trang kết quả


async def get_with_names(db: AsyncSession, review_id: int, lang: str, default_lang: str) -> ReviewRow | None:
    """Một đánh giá kèm tên người viết + tên động vật (trả về sau khi tạo/sửa); không có -> None."""
    row = (await db.execute(_select_with_names(lang, default_lang).where(Review.id == review_id))).first()
    return tuple(row) if row else None


async def summary(db: AsyncSession, animal_id: int | None = None, user_id: int | None = None,
            statuses: list[str] | None = None, user_name: str | None = None,
            visible_only: bool = False) -> tuple[float | None, int]:
    """Điểm trung bình và tổng số đánh giá khớp CÙNG bộ lọc với list_reviews (không phân trang).

    Trả về: (điểm trung bình, tổng số); không có đánh giá nào -> (None, 0).
    """
    stmt = (select(Review.rating)
            .join(User, User.id == Review.user_id)
            .join(Animal, Animal.id == Review.animal_id))
    sub = _apply_filters(stmt, animal_id, user_id, statuses, user_name, visible_only).subquery()
    avg, count = (await db.execute(select(func.avg(sub.c.rating), func.count()))).one()  # await: chờ SQLite tính
    return avg, count


async def add(db: AsyncSession, review: Review) -> Review:
    """Thêm đánh giá; flush để CSDL cấp review.id (chưa commit)."""
    db.add(review)
    await db.flush()
    return review


async def delete(db: AsyncSession, review: Review) -> None:
    """Xóa vĩnh viễn một đánh giá."""
    await db.delete(review)
    await db.flush()
