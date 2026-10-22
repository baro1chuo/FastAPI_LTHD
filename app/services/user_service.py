"""Nghiệp vụ tài khoản: đăng ký (UC06), hồ sơ (UC08), quản lý tài khoản của admin (UC14)."""
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, ConflictError, ForbiddenError, NotFoundError
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories import user_repository
from app.schemas.user import UserCreate, UserProfileUpdate, UserStatusUpdate


def create_user(db: Session, data: UserCreate) -> User:
    """UC06 – đăng ký. Email chuẩn hóa chữ thường, đã tồn tại -> ConflictError 409.

    Tài khoản tự đăng ký luôn có vai trò 'user', trạng thái 'active'; chỉ lưu hash mật khẩu.
    """
    email = data.email.lower()
    if user_repository.get_by_email(db, email):
        raise ConflictError("Email đã được sử dụng")
    role = user_repository.get_role_by_code(db, "user")
    user = user_repository.add(db, User(
        full_name=data.full_name.strip(),
        email=email,
        avatar=data.avatar,
        role_id=role.id,
        password_hash=hash_password(data.password.get_secret_value()),
    ))
    db.commit()
    db.refresh(user)  # nạp status, created_at do CSDL tự điền
    return user


def update_profile(db: Session, current_user: User, data: UserProfileUpdate) -> User:
    """UC08 – sửa họ tên, ảnh đại diện và/hoặc đổi mật khẩu của chính mình (email không sửa được).

    Đổi mật khẩu phải nhập đúng mật khẩu hiện tại, sai -> BusinessRuleError 400.
    """
    if data.full_name is not None:
        current_user.full_name = data.full_name.strip()
    if data.avatar is not None:
        current_user.avatar = data.avatar
    if data.password is not None:
        if not verify_password(data.password.current_password.get_secret_value(), current_user.password_hash):
            raise BusinessRuleError("Mật khẩu hiện tại không đúng")
        current_user.password_hash = hash_password(data.password.new_password.get_secret_value())
    db.commit()
    return current_user


def list_users(db: Session, search: str | None = None, status: str | None = None,
               page: int = 1, size: int = 20) -> list[User]:
    """UC14 – danh sách tài khoản: tìm theo tên/email, lọc trạng thái, phân trang (page bắt đầu từ 1)."""
    return user_repository.list_users(db, search, status, offset=(page - 1) * size, limit=size)


def get_user(db: Session, user_id: int) -> User:
    """UC14 – chi tiết một tài khoản; không có -> NotFoundError 404."""
    user = user_repository.get_by_id(db, user_id)
    if user is None:
        raise NotFoundError("Không tìm thấy tài khoản")
    return user


def set_status(db: Session, admin: User, user_id: int, data: UserStatusUpdate) -> User:
    """UC14 – khóa / mở khóa / đổi vai trò. Admin không được tự sửa chính mình (403).

    role_id không tồn tại -> NotFoundError 404. Tài khoản 'locked' sẽ không đăng nhập được.
    """
    if admin.id == user_id:
        raise ForbiddenError("Không thể tự khóa hoặc đổi vai trò của chính mình")
    user = get_user(db, user_id)
    if data.status is not None:
        user.status = data.status.value
    if data.role_id is not None:
        role = user_repository.get_role_by_id(db, data.role_id)
        if role is None:
            raise NotFoundError("Không tìm thấy vai trò")
        user.role = role
    db.commit()
    return user


def delete_user(db: Session, admin: User, user_id: int) -> None:
    """UC14 – xóa tài khoản (đánh giá của tài khoản bị xóa theo). Tự xóa mình -> 403, không có -> 404."""
    if admin.id == user_id:
        raise ForbiddenError("Không thể tự xóa chính mình")
    user_repository.delete(db, get_user(db, user_id))
    db.commit()
