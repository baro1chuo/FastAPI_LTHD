"""Tầng router – nhóm API NGƯỜI DÙNG (/api/users). Router mỏng: nhận request, kiểm tra quyền, gọi user_service."""
from fastapi import APIRouter, Depends, File, Query, UploadFile, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_admin
from app.schemas.user import UserAdminResponse, UserProfileUpdate, UserResponse, UserStatus, UserStatusUpdate
from app.services import user_service

router = APIRouter(
    prefix="/api/users",
    tags=["Users"],
)

# ----- NGƯỜI DÙNG ĐÃ ĐĂNG NHẬP -----
# Khai báo /me TRƯỚC /{user_id}: FastAPI so đường dẫn theo thứ tự khai báo
@router.get("/me", response_model=UserResponse)
def get_me(current_user=Depends(get_current_user)):
    """UC08 – xem hồ sơ của chính mình (id lấy từ JWT)."""
    return current_user


@router.patch("/me", response_model=UserResponse)
def update_me(
    data: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """UC08 – sửa họ tên, ảnh đại diện, đổi mật khẩu (gửi kèm object password). Không sửa email.
    400 nếu sai mật khẩu hiện tại."""
    return user_service.update_profile(db, current_user, data)


@router.post("/{user_id}/image", response_model=UserResponse)
def upload_avatar(
    user_id: int,
    file: UploadFile = File(..., description="Ảnh JPEG/PNG/WEBP/GIF, tối đa 2 MB"),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """UC08 – tải ảnh đại diện (multipart/form-data, field `file`) cho chính mình.
    403 nếu user_id không phải của mình, 400 nếu không phải ảnh hợp lệ / quá dung lượng."""
    return user_service.upload_avatar(db, current_user, user_id, file)


# ----- ADMIN -----
@router.get("", response_model=list[UserAdminResponse])
def list_users(
    search: str | None = Query(None, description="Tìm theo họ tên hoặc email"),
    status: UserStatus | None = None,
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """UC14 – danh sách tài khoản, có tìm kiếm, lọc trạng thái, phân trang."""
    return user_service.list_users(db, search, status.value if status else None, page, size)


@router.get("/{user_id}", response_model=UserAdminResponse)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """UC14 – chi tiết một tài khoản; 404 nếu không có."""
    return user_service.get_user(db, user_id)


@router.patch("/{user_id}/status", response_model=UserAdminResponse)
def update_user_status(
    user_id: int,
    data: UserStatusUpdate,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """UC14 – khóa / mở khóa tài khoản; 403 nếu admin tự khóa mình, 404 nếu không có."""
    return user_service.set_status(db, admin, user_id, data)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """UC14 – xóa tài khoản (kèm đánh giá); 403 nếu admin tự xóa mình, 404 nếu không có."""
    user_service.delete_user(db, admin, user_id)
