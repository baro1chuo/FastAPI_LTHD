"""Tầng router – nhóm API ĐÁNH GIÁ (/api/reviews). Router mỏng: nhận request, kiểm tra quyền, gọi review_service."""
from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.schemas.review import (
    ReviewCreate,
    ReviewPage,
    ReviewResponse,
    ReviewStatus,
    ReviewStatusUpdate,
    ReviewUpdate,
)
from app.services import review_service

router = APIRouter(prefix="/api/reviews", tags=["Reviews"])

# --- Guest (công khai) ---
@router.get("", response_model=ReviewPage)
def list_public_reviews(
    animal_id: int = Query(..., description="Đánh giá của động vật nào"),
    lang: str = Query("vi"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """UC04 – đánh giá ĐÃ DUYỆT của một động vật, kèm tên người viết, tổng số và điểm trung bình.
    404 nếu động vật không có hoặc đang ẩn."""
    return review_service.list_approved(db, animal_id, lang, page, size)


# --- Người dùng đã đăng nhập (User, Admin) ---
@router.get("/me", response_model=list[ReviewResponse])
def list_my_reviews(
    lang: str = Query("vi"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """UC10 – mọi đánh giá của chính mình (kể cả chờ duyệt / đã ẩn), kèm tên động vật."""
    return review_service.list_by_user(db, current_user, lang)


@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_review(
    data: ReviewCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """UC09 – gửi đánh giá. 404 động vật không có/đang ẩn, 409 đã đánh giá; tự duyệt nếu cài đặt bật."""
    return review_service.create_review(db, current_user, data)


@router.patch("/me/{review_id}", response_model=ReviewResponse)
def update_my_review(
    review_id: int,
    data: ReviewUpdate,
    lang: str = Query("vi"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """UC12 – sửa rating/comment đánh giá của chính mình; trạng thái về chờ duyệt (trừ khi tự duyệt bật).
    403 nếu không phải của mình, 404 nếu không có."""
    return review_service.update_my_review(db, current_user, review_id, data, lang)


@router.delete("/me/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_my_review(
    review_id: int,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """UC12 – xóa đánh giá của chính mình. 403 nếu không phải của mình, 404 nếu không có."""
    review_service.delete_my_review(db, current_user, review_id)


# --- Admin ---
@router.get("/all", response_model=ReviewPage)
def list_all_reviews(
    status_filter: ReviewStatus | None = Query(None, alias="status"),
    animal_id: int | None = Query(None),
    lang: str = Query("vi"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """UC13 – admin xem mọi đánh giá, lọc theo trạng thái / động vật, kèm tên người viết và tên động vật."""
    return review_service.list_all(db, status_filter, animal_id, lang, page, size)


@router.get("/search", response_model=ReviewPage)
def search_reviews(
    username: str = Query(..., min_length=1, description="Tên người viết (tìm gần đúng)"),
    lang: str = Query("vi"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """UC13 – admin tìm đánh giá theo tên người viết."""
    return review_service.search_by_username(db, username, lang, page, size)


@router.patch("/{review_id}", response_model=ReviewResponse)
def moderate_review(
    review_id: int,
    data: ReviewStatusUpdate,
    lang: str = Query("vi"),
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """UC13 – duyệt (approved) hoặc ẩn (hidden) đánh giá. 404 nếu không có."""
    return review_service.set_status(db, review_id, data, lang)


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """UC13 – admin xóa vĩnh viễn đánh giá. 404 nếu không có."""
    review_service.delete_review(db, review_id)
