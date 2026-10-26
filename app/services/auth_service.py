"""Tầng service – UC07 Đăng nhập.

UC05 Đăng xuất không cần service: JWT không lưu trên server nên frontend tự xóa token (router chỉ trả 204).
"""
from fastapi.concurrency import run_in_threadpool
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import AuthError, ForbiddenError
from app.core.security import create_access_token, verify_password
from app.repositories import user_repository
from app.schemas.auth import LoginRequest


async def login(db: AsyncSession, data: LoginRequest) -> str:
    """UC07 – kiểm tra email + mật khẩu, trả access token (JWT) chứa id và vai trò.

    Trả về: chuỗi JWT. Lỗi: AuthError (401) – sai email hoặc mật khẩu (thông báo CHUNG để không lộ
    email nào đã đăng ký, UC07 E2); ForbiddenError (403) – tài khoản bị khóa (UC07 E3).
    """
    user = await user_repository.get_by_email(db, data.email.lower())  # await: chờ SQLite tìm user
    # run_in_threadpool: PBKDF2 600.000 vòng là việc NẶNG CPU (~0,3–0,5 giây); gọi thẳng trong async def
    # sẽ chặn event loop, mọi request khác phải đứng chờ. Đẩy sang luồng phụ để event loop tiếp tục phục vụ.
    if user is None or not await run_in_threadpool(verify_password, data.password, user.password_hash):
        raise AuthError("Email hoặc mật khẩu không đúng")
    if user.status == "locked":
        raise ForbiddenError("Tài khoản đã bị khóa")
    # Tạo JWT là phép tính nhanh (HMAC-SHA256) nên gọi thẳng, không cần await
    return create_access_token(user.id, user.role.code)
