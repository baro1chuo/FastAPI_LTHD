from fastapi import APIRouter, Depends, Query, Response, status
from sqlalchemy.orm import Session

from app.___.database import get_db
from app.___.deps import get_current_user, require_admin
from app.routers import not_implemented
from app.schema.review import (
    ReviewCreate,
    ReviewOut,
    ReviewStatus,
    ReviewStatusUpdate,
)

router = APIRouter(prefix="/api/reviews", tags=["Reviews"])

# --- Guest (cong khai)  ---
@router.get("", response_model=list[ReviewOut])
def list_public_reviews():



# --- Nguoi dung da dang nhap  ---
@router.get("/me", response_model=list[ReviewOut])
def list_my_reviews():

@router.post("", response_model=ReviewOut, status_code=status.HTTP_201_CREATED)
def create_review():

# --- Admin ---
@router.get("/all", response_model=list[ReviewOut])
def list_all_reviews():

@router.patch("/{review_id}", response_model=ReviewOut)
def moderate_review():

@router.delete("/{review_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_review():