from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_admin # lay nguoi dung hien tai, yeu cau admin tu ben depend
from app.schemas.user import UserAdminResponse, UserProfileUpdate, UserResponse, UserStatus, UserStatusUpdate
from app.services import user_service

router = APIRouter(
    prefix="/api/users",
    tags=["Users"],
)

# -----DOI VOI NGUOI DUNG DA DANG NHAP-----
@router.put("/update/me", response_model=UserResponse) #Cap nhat tai khoan ca nhan
def update_me(
    data: UserProfileUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """UC08 – sửa họ tên, ảnh đại diện, đổi mật khẩu (gửi kèm object password)."""
    return user_service.update_profile(db, current_user, data)


# -----CHI DE TEST (khong can dang nhap) – XOA TRUOC KHI NOP/TRIEN KHAI-----
@router.get("/test/all", response_model=list[UserAdminResponse])
def list_users_for_test(db: Session = Depends(get_db)):
    """CHỈ ĐỂ TEST: xem mọi tài khoản mà không cần token admin (không trả mật khẩu/hash)."""
    return user_service.list_users(db, size=1000)


# -----DOI VOI ADMIN-----
@router.get("", response_model=list[UserAdminResponse]) #Xem danh sach
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


@router.get("/{user_id}", response_model=UserAdminResponse) #Tim 1 user
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """UC14 – chi tiết một tài khoản; 404 nếu không có."""
    return user_service.get_user(db, user_id)


@router.patch("/{user_id}", response_model=UserAdminResponse) #Khoa/mo khoa/doi vai tro
def update_user(
    user_id: int,
    data: UserStatusUpdate,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """UC14 – khóa / mở khóa / đổi vai trò; 403 nếu admin tự sửa mình, 404 nếu không có user/vai trò."""
    return user_service.set_status(db, admin, user_id, data)


@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT) #Xoa tai khoan
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """UC14 – xóa tài khoản (kèm đánh giá); 403 nếu admin tự xóa mình, 404 nếu không có."""
    user_service.delete_user(db, admin, user_id)
