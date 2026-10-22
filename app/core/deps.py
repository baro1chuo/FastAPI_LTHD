"""Tầng core – dependency xác thực (đọc JWT) và phân quyền (Guest / User / Admin) cho router."""
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


def _user_from_token(db: Session, token: str) -> User:
    """Giải mã JWT rồi lấy user trong CSDL.

    Lỗi: AuthError (401) – token sai/hết hạn hoặc user đã bị xóa;
    ForbiddenError (403) – tài khoản bị khóa (chặn ngay cả khi token cũ chưa hết hạn).
    """
    user = user_repository.get_by_id(db, decode_access_token(token))
    if user is None:
        raise AuthError("Tài khoản không tồn tại")
    if user.status == "locked":
        raise ForbiddenError("Tài khoản đã bị khóa")
    return user


def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User:
    """Dependency cho API cần đăng nhập (User, Admin): trả user đang đăng nhập.

    Lỗi: 401 nếu thiếu/sai token; 403 nếu tài khoản bị khóa.
    """
    if credentials is None:
        raise AuthError("Chưa đăng nhập")
    return _user_from_token(db, credentials.credentials)


def get_optional_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    db: Session = Depends(get_db),
) -> User | None:
    """Dependency cho API công khai mà admin được xem thêm (vd danh sách động vật gồm cả động vật ẩn).

    Không gửi token -> None (Guest). Có gửi token thì kiểm tra như get_current_user (401/403 nếu sai/bị khóa).
    """
    if credentials is None:
        return None
    return _user_from_token(db, credentials.credentials)


def is_admin(user: User | None) -> bool:
    """True nếu user là admin; Guest (None) và User thường -> False."""
    return user is not None and user.role.code == "admin"


def require_admin(current_user: User = Depends(get_current_user)) -> User:
    """Dependency cho API chỉ Admin dùng; vai trò khác -> ForbiddenError (403)."""
    if not is_admin(current_user):
        raise ForbiddenError("Chỉ admin mới có quyền này")
    return current_user
