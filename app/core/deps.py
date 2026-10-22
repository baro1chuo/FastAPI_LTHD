"""Dependency xác thực và phân quyền cho router."""
from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.exceptions import AuthError, ForbiddenError
from app.core.security import decode_access_token
from app.models.user import User
from app.repositories import user_repository

# Đọc header "Authorization: Bearer <token>"; auto_error=False để tự trả 401 theo định dạng chung
_bearer = HTTPBearer(auto_error=False)


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Lấy user đang đăng nhập từ JWT.

    Thiếu/sai token hoặc user không còn tồn tại -> 401; tài khoản bị khóa -> 403
    (khóa có hiệu lực ngay cả khi token cũ chưa hết hạn).
    """
    if credentials is None:
        raise AuthError("Chưa đăng nhập")
    user = user_repository.get_by_id(db, decode_access_token(credentials.credentials))
    if user is None:
        raise AuthError("Tài khoản không tồn tại")
    if user.status == "locked":
        raise ForbiddenError("Tài khoản đã bị khóa")
    return user


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Chỉ cho admin đi tiếp; vai trò khác -> 403."""
    if current_user.role.code != "admin":
        raise ForbiddenError("Chỉ admin mới có quyền này")
    return current_user
