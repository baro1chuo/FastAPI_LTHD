"""Truy vấn bảng REVIEW. Không chứa quy tắc nghiệp vụ, không commit."""
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.models.review import Review


def get_by_id(db: Session, review_id: int) -> Review | None:
    """Lấy đánh giá theo id; không có thì trả None."""
    return db.get(Review, review_id)


def get_by_user_and_animal(db: Session, user_id: int, animal_id: int) -> Review | None:
    """Đánh giá của user cho động vật này (UNIQUE(animalId, userId)); chưa có thì trả None."""
    return db.scalar(select(Review).where(Review.user_id == user_id, Review.animal_id == animal_id))


def _filtered(animal_id: int | None, user_id: int | None, statuses: list[str] | None):
    """Câu SELECT đánh giá đã áp các bộ lọc; bộ lọc nào None thì bỏ qua."""
    stmt = select(Review)
    if animal_id is not None:
        stmt = stmt.where(Review.animal_id == animal_id)
    if user_id is not None:
        stmt = stmt.where(Review.user_id == user_id)
    if statuses:
        stmt = stmt.where(Review.status.in_(statuses))
    return stmt


def list_reviews(db: Session, animal_id: int | None = None, user_id: int | None = None,
                 statuses: list[str] | None = None, offset: int = 0, limit: int = 20) -> list[Review]:
    """Danh sách đánh giá theo động vật / người viết / trạng thái, mới nhất trước, có phân trang."""
    stmt = _filtered(animal_id, user_id, statuses)
    return list(db.scalars(stmt.order_by(Review.created_at.desc(), Review.id.desc()).offset(offset).limit(limit)))


def summary(db: Session, animal_id: int | None = None, user_id: int | None = None,
            statuses: list[str] | None = None) -> tuple[float | None, int]:
    """Điểm trung bình và tổng số đánh giá khớp bộ lọc. Không có đánh giá nào -> (None, 0)."""
    sub = _filtered(animal_id, user_id, statuses).subquery()
    avg, count = db.execute(select(func.avg(sub.c.rating), func.count())).one()
    return avg, count


def add(db: Session, review: Review) -> Review:
    """Thêm đánh giá; flush để có review.id, service tự commit."""
    db.add(review)
    db.flush()
    return review


def delete(db: Session, review: Review) -> None:
    """Xóa vĩnh viễn một đánh giá."""
    db.delete(review)
    db.flush()
