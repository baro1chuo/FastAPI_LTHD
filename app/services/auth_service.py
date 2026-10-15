"""UC07 Đăng nhập. UC04 Đăng xuất không cần service: JWT không lưu trên server, frontend tự xóa token."""
from sqlalchemy.orm import Session

from app.core.exceptions import AuthError, ForbiddenError
from app.core.security import create_access_token, verify_password
from app.repositories import user_repository
from app.schemas.auth import LoginRequest


def login(db: Session, data: LoginRequest) -> str:
    """Kiểm tra email + mật khẩu, trả access token (JWT) chứa id và vai trò.

    Sai email hoặc mật khẩu -> AuthError 401 (thông báo chung, không lộ email nào tồn tại).
    Tài khoản bị khóa -> ForbiddenError 403.
    """
    user = user_repository.get_by_email(db, data.email.lower())
    if user is None or not verify_password(data.password, user.password_hash):
        raise AuthError("Email hoặc mật khẩu không đúng")
    if user.status == "locked":
        raise ForbiddenError("Tài khoản đã bị khóa")
    return create_access_token(user.id, user.role.code)
