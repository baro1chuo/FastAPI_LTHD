"""Tầng service – nghiệp vụ tài khoản: UC06 Đăng ký, UC08 Xem/cập nhật hồ sơ, UC14 Quản lý tài khoản (admin)."""
from fastapi import UploadFile
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import BusinessRuleError, ConflictError, ForbiddenError, NotFoundError
from app.core.security import hash_password, verify_password
from app.models.user import User
from app.repositories import user_repository
from app.schemas.user import UserCreate, UserProfileUpdate, UserStatusUpdate
from app.services import image_service


async def create_user(db: AsyncSession, data: UserCreate) -> User:
    """UC06 – Đăng ký tài khoản.

    Email chuẩn hóa chữ thường; tài khoản mới luôn có vai trò 'user', trạng thái 'active'; chỉ lưu HASH mật khẩu.
    Trả về: User vừa tạo. Lỗi: ConflictError (409) – email đã tồn tại; 422 – dữ liệu sai (Pydantic).
    """
    email = data.email.lower()
    # Kiểm tra trùng email ở service để trả 409 dễ hiểu (CSDL cũng chặn bằng UNIQUE)
    if await user_repository.get_by_email(db, email):  # await: chờ SQLite tìm email
        raise ConflictError("Email đã được sử dụng")
    role = await user_repository.get_role_by_code(db, "user")
    # run_in_threadpool: PBKDF2 600.000 vòng là việc NẶNG CPU (~0,3–0,5 giây); gọi thẳng trong async def
    # sẽ chặn event loop, mọi request khác phải đứng chờ. Đẩy sang luồng phụ để event loop tiếp tục phục vụ.
    password_hash = await run_in_threadpool(hash_password, data.password.get_secret_value())
    user = await user_repository.add(db, User(
        full_name=data.full_name.strip(),
        email=email,
        avatar=data.avatar,
        role_id=role.id,
        password_hash=password_hash,
    ))
    await db.commit()  # commit ở service: repository chỉ add/flush, service quyết định khi nào lưu hẳn
    # refresh: nạp lại status, created_at do CSDL tự điền (server_default). Với async phải nạp tường minh,
    # nếu đọc thuộc tính chưa nạp sẽ lỗi MissingGreenlet
    await db.refresh(user)
    return user


async def update_profile(db: AsyncSession, current_user: User, data: UserProfileUpdate) -> User:
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
        # run_in_threadpool: kiểm tra và băm mật khẩu đều nặng CPU, chạy ở luồng phụ để không chặn event loop
        if not await run_in_threadpool(verify_password, data.password.current_password.get_secret_value(),
                                       current_user.password_hash):
            raise BusinessRuleError("Mật khẩu hiện tại không đúng")
        current_user.password_hash = await run_in_threadpool(
            hash_password, data.password.new_password.get_secret_value())
    await db.commit()  # await: chờ SQLite ghi thay đổi
    return current_user


async def upload_avatar(db: AsyncSession, current_user: User, user_id: int, upload: UploadFile) -> User:
    """UC08 – Tải ảnh đại diện (multipart/form-data) cho CHÍNH MÌNH; lưu file rồi ghi đường dẫn vào cột avatar.

    Lỗi: ForbiddenError (403) – user_id trên URL không phải của người đang đăng nhập;
    BusinessRuleError (400) – không phải ảnh hợp lệ hoặc vượt dung lượng.
    """
    # Kiểm tra quyền sở hữu: id trên URL phải trùng id lấy từ JWT, không cho đổi ảnh người khác
    if user_id != current_user.id:
        raise ForbiddenError("Chỉ được đổi ảnh đại diện của chính mình")
    current_user.avatar = await image_service.save_image(upload, "avatars")  # await: chờ đọc + lưu file
    await db.commit()
    return current_user


async def list_users(db: AsyncSession, search: str | None = None, status: str | None = None,
                     page: int = 1, size: int = 20) -> list[User]:
    """UC14 – Danh sách tài khoản: tìm theo tên/email, lọc trạng thái, phân trang (page bắt đầu từ 1)."""
    return await user_repository.list_users(db, search, status, offset=(page - 1) * size, limit=size)


async def get_user(db: AsyncSession, user_id: int) -> User:
    """UC14 – Chi tiết một tài khoản. Lỗi: NotFoundError (404) nếu không có."""
    user = await user_repository.get_by_id(db, user_id)
    if user is None:
        raise NotFoundError("Không tìm thấy tài khoản")
    return user


async def set_status(db: AsyncSession, admin: User, user_id: int, data: UserStatusUpdate) -> User:
    """UC14 – Khóa ('locked') / mở khóa ('active') tài khoản. Tài khoản bị khóa không đăng nhập được.

    Lỗi: ForbiddenError (403) – admin tự khóa chính mình (UC14 E1); NotFoundError (404) – không có tài khoản.
    """
    # So id admin (lấy từ JWT) với id bị khóa: chặn admin tự khóa mình rồi không ai mở được
    if admin.id == user_id:
        raise ForbiddenError("Không thể tự khóa tài khoản của chính mình")
    user = await get_user(db, user_id)
    user.status = data.status.value
    await db.commit()
    return user


async def delete_user(db: AsyncSession, admin: User, user_id: int) -> None:
    """UC14 A2 – Xóa tài khoản; đánh giá của tài khoản bị xóa theo (ON DELETE CASCADE).

    Lỗi: ForbiddenError (403) – admin tự xóa chính mình; NotFoundError (404) – không có tài khoản.
    """
    if admin.id == user_id:
        raise ForbiddenError("Không thể tự xóa chính mình")
    await user_repository.delete(db, await get_user(db, user_id))
    await db.commit()
