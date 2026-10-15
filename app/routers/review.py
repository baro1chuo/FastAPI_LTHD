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
)
from app.services import review_service

router = APIRouter(prefix="/api/reviews", tags=["Reviews"])

# --- Guest (cong khai)  ---
@router.get("", response_model=ReviewPage)
def list_public_reviews(
    animal_id: int | None = Query(None, description="Đánh giá của một động vật"),
    user_id: int | None = Query(None, description="Đánh giá của một người dùng"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """UC05 – đánh giá ĐÃ DUYỆT, kèm tổng số và điểm trung bình."""
    return review_service.list_approved(db, animal_id, user_id, page, size)


# --- Nguoi dung da dang nhap  ---
@router.get("/me", response_model=list[ReviewResponse])
def list_my_reviews(
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """UC10 – mọi đánh giá của chính mình, kể cả đang chờ duyệt hoặc bị ẩn."""
    return review_service.list_by_user(db, current_user)


@router.post("", response_model=ReviewResponse, status_code=status.HTTP_201_CREATED)
def create_review(
    data: ReviewCreate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """UC09 – gửi đánh giá. 404 không có động vật, 409 đã đánh giá; tự duyệt nếu cài đặt bật."""
    return review_service.create_review(db, current_user, data)


# --- Admin ---
@router.get("/all", response_model=ReviewPage)
def list_all_reviews(
    status_filter: ReviewStatus | None = Query(None, alias="status"),
    animal_id: int | None = Query(None),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """UC13 – admin xem mọi đánh giá, lọc theo trạng thái / động vật."""
    return review_service.list_all(db, status_filter, animal_id, page, size)


@router.patch("/{review_id}", response_model=ReviewResponse)
def moderate_review(
    review_id: int,
    data: ReviewStatusUpdate,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """UC13 – duyệt (approved) hoặc ẩn (hidden) đánh giá."""
    return review_service.set_status(db, review_id, data)


@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """UC13 – xóa vĩnh viễn đánh giá."""
    review_service.delete_review(db, review_id)
