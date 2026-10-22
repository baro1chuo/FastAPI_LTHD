"""Tầng service – nghiệp vụ tài khoản: UC06 Đăng ký, UC08 Xem/cập nhật hồ sơ, UC14 Quản lý tài khoản (admin)."""
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, ConflictError, ForbiddenError, NotFoundError
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories import user_repository
from app.schemas.user import UserCreate, UserProfileUpdate, UserStatusUpdate
from app.services import image_service


def create_user(db: Session, data: UserCreate) -> User:
    """UC06 – Đăng ký tài khoản.

    Email chuẩn hóa chữ thường; tài khoản mới luôn có vai trò 'user', trạng thái 'active'; chỉ lưu HASH mật khẩu.
    Trả về: User vừa tạo. Lỗi: ConflictError (409) – email đã tồn tại; 422 – dữ liệu sai (Pydantic).
    """
    email = data.email.lower()
    # Kiểm tra trùng email ở service để trả 409 dễ hiểu (CSDL cũng chặn bằng UNIQUE)
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
    db.commit()  # commit ở service: repository chỉ add/flush
    db.refresh(user)  # nạp lại status, created_at do CSDL tự điền (server_default)
    return user


def update_profile(db: Session, current_user: User, data: UserProfileUpdate) -> User:
    """UC08 – Cập nhật hồ sơ của chính mình: họ tên, ảnh đại diện, đổi mật khẩu (A1). Email KHÔNG sửa được.

    current_user lấy từ JWT nên chỉ sửa được hồ sơ của chính mình. Chỉ field được gửi mới đổi.
    Trả về: User sau khi sửa. Lỗi: BusinessRuleError (400) – sai mật khẩu hiện tại (UC08 E2); 422 – dữ liệu sai.
    """
    fields = data.model_fields_set  # tập field client thật sự gửi lên
    if "full_name" in fields:
        current_user.full_name = data.full_name.strip()
    if "avatar" in fields:
        current_user.avatar = data.avatar  # null -> xóa ảnh đại diện
    if data.password is not None:
        # Phải đúng mật khẩu hiện tại mới cho đổi: tránh người khác dùng máy đang đăng nhập để đổi mật khẩu
        if not verify_password(data.password.current_password.get_secret_value(), current_user.password_hash):
            raise BusinessRuleError("Mật khẩu hiện tại không đúng")
        current_user.password_hash = hash_password(data.password.new_password.get_secret_value())
    db.commit()
    return current_user


def upload_avatar(db: Session, current_user: User, user_id: int, upload: UploadFile) -> User:
    """UC08 – Tải ảnh đại diện (multipart/form-data) cho CHÍNH MÌNH; lưu file rồi ghi đường dẫn vào cột avatar.

    Lỗi: ForbiddenError (403) – user_id trên URL không phải của người đang đăng nhập;
    BusinessRuleError (400) – không phải ảnh hợp lệ hoặc vượt dung lượng.
    """
    # Kiểm tra quyền sở hữu: id trên URL phải trùng id lấy từ JWT, không cho đổi ảnh người khác
    if user_id != current_user.id:
        raise ForbiddenError("Chỉ được đổi ảnh đại diện của chính mình")
    current_user.avatar = image_service.save_image(upload, "avatars")
    db.commit()
    return current_user


def list_users(db: Session, search: str | None = None, status: str | None = None,
               page: int = 1, size: int = 20) -> list[User]:
    """UC14 – Danh sách tài khoản: tìm theo tên/email, lọc trạng thái, phân trang (page bắt đầu từ 1)."""
    return user_repository.list_users(db, search, status, offset=(page - 1) * size, limit=size)


def get_user(db: Session, user_id: int) -> User:
    """UC14 – Chi tiết một tài khoản. Lỗi: NotFoundError (404) nếu không có."""
    user = user_repository.get_by_id(db, user_id)
    if user is None:
        raise NotFoundError("Không tìm thấy tài khoản")
    return user


def set_status(db: Session, admin: User, user_id: int, data: UserStatusUpdate) -> User:
    """UC14 – Khóa ('locked') / mở khóa ('active') tài khoản. Tài khoản bị khóa không đăng nhập được.

    Lỗi: ForbiddenError (403) – admin tự khóa chính mình (UC14 E1); NotFoundError (404) – không có tài khoản.
    """
    # So id admin (lấy từ JWT) với id bị khóa: chặn admin tự khóa mình rồi không ai mở được
    if admin.id == user_id:
        raise ForbiddenError("Không thể tự khóa tài khoản của chính mình")
    user = get_user(db, user_id)
    user.status = data.status.value
    db.commit()
    return user


def delete_user(db: Session, admin: User, user_id: int) -> None:
    """UC14 A2 – Xóa tài khoản; đánh giá của tài khoản bị xóa theo (ON DELETE CASCADE).

    Lỗi: ForbiddenError (403) – admin tự xóa chính mình; NotFoundError (404) – không có tài khoản.
    """
    if admin.id == user_id:
        raise ForbiddenError("Không thể tự xóa chính mình")
    user_repository.delete(db, get_user(db, user_id))
    db.commit()
