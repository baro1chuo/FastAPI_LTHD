from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.___.database import get_db
from app.___.deps import get_current_user, require_admin
from app.routers import not_implemented
from app.schemas.review import (
    ReviewCreate,
    ReviewOut,
    ReviewStatus,
    ReviewStatusUpdate,
)

router = APIRouter(prefix="/api/reviews", tags=["Reviews"])

# --- Guest (cong khai)  ---
@router.get("", response_model=list[ReviewOut])
def list_public_reviews(
    animal_id: int = Query(..., description="Đánh giá của một động vật"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db)
):
    not_implemented("review_service.list_approved")



# --- Nguoi dung da dang nhap  ---
@router.get("/me", response_model=list[ReviewOut])
def list_my_reviews(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user),
):
    # Trả cả đánh giá đang chờ duyệt của chính mình
    not_implemented("review_service.list_by_user")

@router.post("", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def create_review(
    data: ReviewCreate,
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
):
    # TODO: review_service.create_review -> 409 nếu đã đánh giá động vật này;
    #tự duyệt nếu settings.auto_approve_reviews = true
    not_implemented("review_service.create_review")

# --- Admin ---
@router.get("/all", response_model=list[ReviewOut])
def list_all_reviews(
    status_filter: ReviewStatus | None = Query(None, alias="status"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin = Depends(require_admin),
):
    not_implemented("review_service.list_all")

@router.patch("/{review_id}", response_model=ReviewOut)
def moderate_review(
    review_id: int,
    data: ReviewStatusUpdate,
    db: Session = Depends(get_db),
    admin = Depends(require_admin),
):
    # Duyệt (approved) hoặc ẩn (hidden)
    not_implemented("review_service.set_status")

@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review(
    review_id: int,
    db: Session = Depends(get_db),
    admin = Depends(require_admin),
):
    not_implemented("review_service.delete_review")
    return Response(status_code=status.HTTP_204_NO_CONTENT)