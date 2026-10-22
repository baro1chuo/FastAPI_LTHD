"""Nghiệp vụ đánh giá: UC05 Xem, UC09 Gửi, UC10 Đánh giá của tôi, UC13 Duyệt/ẩn/xóa."""
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, NotFoundError
from app.models.user import User
from app.models.review import Review
from app.repositories import animal_repository, review_repository, settings_repository
from app.schemas.review import ReviewCreate, ReviewStatus, ReviewStatusUpdate
from app.services.i18n import resolve_lang


def _page(db: Session, animal_id: int | None, user_id: int | None, statuses: list[str] | None,
          page: int, size: int) -> dict:
    """Danh sách đánh giá theo bộ lọc + tổng số + điểm trung bình (schema ReviewPage)."""
    items = review_repository.list_reviews(db, animal_id, user_id, statuses,
                                           offset=(page - 1) * size, limit=size)
    avg, total = review_repository.summary(db, animal_id, user_id, statuses)
    return {"items": items, "total": total, "average": round(avg, 1) if avg is not None else None}


def list_approved(db: Session, animal_id: int | None = None, user_id: int | None = None,
                  page: int = 1, size: int = 20) -> dict:
    """UC05 – khách chỉ thấy đánh giá ĐÃ DUYỆT; lọc theo động vật và/hoặc người viết."""
    return _page(db, animal_id, user_id, [ReviewStatus.APPROVED.value], page, size)


def list_by_user(db: Session, current_user: User) -> list[Review]:
    """UC10 – chủ đánh giá thấy MỌI trạng thái của mình (chờ duyệt / đã duyệt / đã ẩn)."""
    return review_repository.list_reviews(db, user_id=current_user.id, limit=1000)


def create_review(db: Session, current_user: User, data: ReviewCreate) -> Review:
    """UC09 – gửi đánh giá; user_id lấy từ token, KHÔNG lấy từ body.

    Động vật không có -> 404; đã đánh giá động vật này -> 409 (mỗi người 1 lần).
    Trạng thái: 'approved' nếu cài đặt tự duyệt đang bật, ngược lại 'pending'.
    """
    if animal_repository.get_by_id(db, data.animal_id) is None:
        raise NotFoundError("Không tìm thấy động vật")
    if review_repository.get_by_user_and_animal(db, current_user.id, data.animal_id):
        raise ConflictError("Bạn đã đánh giá động vật này")
    auto_approve = settings_repository.get(db).auto_approve
    review = review_repository.add(db, Review(
        animal_id=data.animal_id,
        user_id=current_user.id,
        rating=data.rating,
        comment=data.comment,
        lang=resolve_lang(db, data.lang),
        status=ReviewStatus.APPROVED.value if auto_approve else ReviewStatus.PENDING.value,
    ))
    db.commit()
    db.refresh(review)  # nạp created_at do CSDL tự điền
    return review


def list_all(db: Session, status: ReviewStatus | None = None, animal_id: int | None = None,
             page: int = 1, size: int = 20) -> dict:
    """UC13 – admin xem mọi đánh giá, lọc theo trạng thái và/hoặc động vật."""
    return _page(db, animal_id, None, [status.value] if status else None, page, size)


def _get_or_404(db: Session, review_id: int) -> Review:
    """Lấy đánh giá theo id; không có -> NotFoundError 404."""
    review = review_repository.get_by_id(db, review_id)
    if review is None:
        raise NotFoundError("Đánh giá không tồn tại hoặc đã bị xóa")
    return review


def set_status(db: Session, review_id: int, data: ReviewStatusUpdate) -> Review:
    """UC13 – duyệt (approved), ẩn (hidden) hoặc đưa về chờ duyệt (pending). 404 nếu không có."""
    review = _get_or_404(db, review_id)
    review.status = data.status.value
    db.commit()
    return review


def delete_review(db: Session, review_id: int) -> None:
    """UC13 – xóa vĩnh viễn một đánh giá. 404 nếu không có."""
    review_repository.delete(db, _get_or_404(db, review_id))
    db.commit()
