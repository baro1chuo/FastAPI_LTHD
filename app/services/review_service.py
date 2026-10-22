"""Tầng service – nghiệp vụ đánh giá: UC04 Xem đánh giá, UC09 Gửi, UC10 Đánh giá của tôi,
UC12 Sửa/xóa đánh giá của tôi, UC13 Duyệt/ẩn/xóa (admin)."""
from sqlalchemy.orm import Session

from app.core.exceptions import ConflictError, ForbiddenError, NotFoundError
from app.models.review import Review
from app.models.user import User
from app.repositories import review_repository, settings_repository
from app.repositories.review_repository import ReviewRow
from app.schemas.review import ReviewCreate, ReviewStatus, ReviewStatusUpdate, ReviewUpdate
from app.services import animal_service
from app.services.i18n import default_lang, resolve_lang


def _to_dict(row: ReviewRow) -> dict:
    """Ghép (Review, tên người viết, tên động vật) thành dict theo schema ReviewResponse."""
    review, user_name, animal_name = row
    return {
        "id": review.id, "animal_id": review.animal_id, "animal_name": animal_name,
        "user_id": review.user_id, "user_name": user_name, "rating": review.rating,
        "comment": review.comment, "status": review.status, "created_at": review.created_at,
        "lang": review.lang,
    }


def _detail(db: Session, review_id: int, lang: str | None) -> dict:
    """Đọc lại một đánh giá kèm tên người viết + tên động vật để trả về sau khi tạo/sửa."""
    return _to_dict(review_repository.get_with_names(db, review_id, resolve_lang(db, lang), default_lang(db)))


def _page(db: Session, lang: str | None, page: int, size: int, **filters) -> dict:
    """Danh sách đánh giá theo bộ lọc + tổng số + điểm trung bình (schema ReviewPage).

    filters: animal_id, user_id, statuses, user_name, visible_only (truyền thẳng xuống repository).
    """
    rows = review_repository.list_reviews(db, resolve_lang(db, lang), default_lang(db),
                                          offset=(page - 1) * size, limit=size, **filters)
    # Tổng số và điểm trung bình tính trên TOÀN BỘ kết quả lọc, không chỉ trang hiện tại
    avg, total = review_repository.summary(db, **filters)
    return {"items": [_to_dict(r) for r in rows], "total": total,
            "average": round(avg, 1) if avg is not None else None}


def _auto_status(db: Session) -> str:
    """Trạng thái cho đánh giá mới/vừa sửa: 'approved' nếu cài đặt tự duyệt đang bật, ngược lại 'pending'.

    Đọc cài đặt tại thời điểm gửi nên bật tự duyệt KHÔNG đổi các đánh giá đang chờ (quy tắc UC16).
    """
    return ReviewStatus.APPROVED.value if settings_repository.get(db).auto_approve else ReviewStatus.PENDING.value


def list_approved(db: Session, animal_id: int, lang: str | None = None, page: int = 1, size: int = 20) -> dict:
    """UC04 – Xem đánh giá: đánh giá ĐÃ DUYỆT của một động vật, mới nhất trước, kèm tổng số + điểm TB.

    Trả về: ReviewPage. Lỗi: NotFoundError (404) nếu động vật không có hoặc đang ẩn.
    """
    animal_service.get_visible_animal(db, animal_id)  # động vật ẩn -> 404 như trang chi tiết (UC02 E1)
    return _page(db, lang, page, size, animal_id=animal_id,
                 statuses=[ReviewStatus.APPROVED.value], visible_only=True)


def list_by_user(db: Session, current_user: User, lang: str | None = None) -> list[dict]:
    """UC10 – Xem đánh giá của tôi: MỌI trạng thái (chờ duyệt / đã duyệt / đã ẩn), kèm tên động vật.

    user_id lấy từ JWT nên người dùng chỉ thấy đánh giá của chính mình. Trả về: list ReviewResponse.
    """
    rows = review_repository.list_reviews(db, resolve_lang(db, lang), default_lang(db),
                                          user_id=current_user.id, limit=1000)
    return [_to_dict(r) for r in rows]


def create_review(db: Session, current_user: User, data: ReviewCreate) -> dict:
    """UC09 – Gửi đánh giá; user_id lấy từ token, KHÔNG lấy từ body.

    Trả về: ReviewResponse ('approved' nếu tự duyệt bật, ngược lại 'pending').
    Lỗi: NotFoundError (404) – động vật không có/đang ẩn; ConflictError (409) – đã đánh giá động vật này.
    """
    # Động vật phải tồn tại VÀ đang hiển thị; đang ẩn -> 404 (UC09 E3)
    animal_service.get_visible_animal(db, data.animal_id)
    # Kiểm tra trùng trước để trả 409 dễ hiểu (CSDL cũng chặn bằng UNIQUE(animalId, userId))
    if review_repository.get_by_user_and_animal(db, current_user.id, data.animal_id):
        raise ConflictError("Bạn đã đánh giá động vật này")
    lang = resolve_lang(db, data.lang)
    review = review_repository.add(db, Review(
        animal_id=data.animal_id, user_id=current_user.id, rating=data.rating,
        comment=data.comment, lang=lang, status=_auto_status(db),
    ))
    db.commit()  # commit ở service: repository chỉ add/flush, service quyết định khi nào lưu hẳn
    return _detail(db, review.id, lang)


def _get_or_404(db: Session, review_id: int) -> Review:
    """Lấy đánh giá theo id; không có -> NotFoundError (404)."""
    review = review_repository.get_by_id(db, review_id)
    if review is None:
        raise NotFoundError("Đánh giá không tồn tại hoặc đã bị xóa")
    return review


def _get_own_or_error(db: Session, current_user: User, review_id: int) -> Review:
    """Lấy đánh giá CỦA CHÍNH người đang đăng nhập (UC12 E2).

    Lỗi: NotFoundError (404) – không có/đã bị admin xóa; ForbiddenError (403) – đánh giá của người khác.
    """
    review = _get_or_404(db, review_id)
    # Kiểm tra quyền sở hữu: so user_id của đánh giá với id lấy từ JWT (không tin dữ liệu client gửi)
    if review.user_id != current_user.id:
        raise ForbiddenError("Bạn chỉ được sửa/xóa đánh giá của chính mình")
    return review


def update_my_review(db: Session, current_user: User, review_id: int, data: ReviewUpdate,
                     lang: str | None = None) -> dict:
    """UC12 – Sửa đánh giá của tôi: đổi rating và/hoặc comment (chỉ field được gửi).

    Sau khi sửa, trạng thái về 'pending' để nội dung mới được duyệt lại ('approved' nếu đang bật tự duyệt).
    Trả về: ReviewResponse. Lỗi: 404 không có; 403 không phải của mình; 422 dữ liệu sai (Pydantic).
    """
    review = _get_own_or_error(db, current_user, review_id)
    for field, value in data.model_dump(exclude_unset=True).items():  # chỉ đổi field client gửi
        setattr(review, field, value)
    review.status = _auto_status(db)
    db.commit()
    return _detail(db, review.id, lang)


def delete_my_review(db: Session, current_user: User, review_id: int) -> None:
    """UC12 – Xóa đánh giá của tôi (xóa vĩnh viễn; sau đó được gửi đánh giá mới cho động vật đó).

    Lỗi: 404 không có; 403 không phải của mình.
    """
    review_repository.delete(db, _get_own_or_error(db, current_user, review_id))
    db.commit()


def list_all(db: Session, status: ReviewStatus | None = None, animal_id: int | None = None,
             lang: str | None = None, page: int = 1, size: int = 20) -> dict:
    """UC13 – Admin xem mọi đánh giá (mọi trạng thái, kể cả động vật đang ẩn), lọc trạng thái/động vật.

    Trả về: ReviewPage kèm tên người viết và tên động vật.
    """
    return _page(db, lang, page, size, animal_id=animal_id, statuses=[status.value] if status else None)


def search_by_username(db: Session, username: str, lang: str | None = None,
                       page: int = 1, size: int = 20) -> dict:
    """UC13 – Admin tìm đánh giá theo tên người viết (gần đúng, không phân biệt hoa thường với chữ không dấu).

    Trả về: ReviewPage.
    """
    return _page(db, lang, page, size, user_name=username)


def set_status(db: Session, review_id: int, data: ReviewStatusUpdate, lang: str | None = None) -> dict:
    """UC13 – Duyệt (approved), ẩn (hidden) hoặc đưa về chờ duyệt (pending). Lỗi: 404 nếu không có."""
    review = _get_or_404(db, review_id)
    review.status = data.status.value
    db.commit()
    return _detail(db, review.id, lang)


def delete_review(db: Session, review_id: int) -> None:
    """UC13 – Admin xóa vĩnh viễn một đánh giá. Lỗi: 404 nếu không có."""
    review_repository.delete(db, _get_or_404(db, review_id))
    db.commit()
