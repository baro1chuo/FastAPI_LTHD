from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import get_current_user
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


@router.get("/me", response_model=UserResponse)
def me(current_user=Depends(get_current_user)):
    """Thông tin user đang đăng nhập (lấy từ token)."""
    return current_user
