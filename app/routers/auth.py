"""Tầng router – nhóm API XÁC THỰC (/api/auth): đăng ký, đăng nhập, đăng xuất, xem user hiện tại."""
from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user, require_token
from app.schemas.auth import LoginRequest, TokenResponse
from app.schemas.user import UserCreate, UserResponse
from app.services import auth_service, user_service

router = APIRouter(prefix="/api/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(data: UserCreate, db: Session = Depends(get_db)):
    """UC06 – đăng ký tài khoản mới (vai trò user). 409 nếu trùng email, 422 nếu mật khẩu < 8 ký tự."""
    return user_service.create_user(db, data)


@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
    """UC07 – đăng nhập, trả JWT. 401 sai email/mật khẩu, 403 tài khoản bị khóa."""
    return TokenResponse(token=auth_service.login(db, data))


@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
def logout(user_id: int = Depends(require_token)):
    """UC05 – đăng xuất (User, Admin). Chỉ trả 204, không đụng CSDL.

    JWT không lưu trên server nên server không có gì để xóa: frontend tự xóa token khỏi thiết bị.
    Token đã cấp vẫn hợp lệ tới khi hết hạn (ACCESS_TOKEN_EXPIRE_MINUTES). 401 nếu thiếu/sai token.
    """
    return Response(status_code=status.HTTP_204_NO_CONTENT)


@router.get("/me", response_model=UserResponse)
def me(current_user=Depends(get_current_user)):
    """Thông tin user đang đăng nhập (lấy từ token); giống GET /api/users/me."""
    return current_user
