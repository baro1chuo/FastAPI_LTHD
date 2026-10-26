"""Tầng repository – truy vấn bảng USER và ROLE (async).

Chỉ viết câu truy vấn; không kiểm tra quy tắc nghiệp vụ, không commit (service commit).
"""
from sqlalchemy import or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.role import Role
from app.models.user import User


async def get_by_id(db: AsyncSession, user_id: int) -> User | None:
    """Lấy user theo id (kèm role nhờ lazy="joined"); không có -> None."""
    return await db.get(User, user_id)  # await: chờ SQLite trả dòng user


async def get_by_email(db: AsyncSession, email: str) -> User | None:
    """Tìm user theo email (cột UNIQUE); email truyền vào đã chuẩn hóa chữ thường."""
    return await db.scalar(select(User).where(User.email == email))


async def get_role_by_code(db: AsyncSession, code: str) -> Role | None:
    """Lấy vai trò theo code: 'admin' | 'staff' | 'user'; không có -> None."""
    return await db.scalar(select(Role).where(Role.code == code))


async def list_users(db: AsyncSession, search: str | None = None, status: str | None = None,
                     offset: int = 0, limit: int = 20) -> list[User]:
    """UC14 – danh sách user, mới tạo trước.

    Tham số: search – tìm gần đúng theo họ tên hoặc email; status – 'active' | 'locked';
    offset/limit – phân trang. Trả về: list User.
    """
    stmt = select(User)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(or_(User.full_name.ilike(pattern), User.email.ilike(pattern)))
    if status:
        stmt = stmt.where(User.status == status)
    stmt = stmt.order_by(User.created_at.desc(), User.id.desc()).offset(offset).limit(limit)
    return list(await db.scalars(stmt))  # await: chờ SQLite trả danh sách


async def add(db: AsyncSession, user: User) -> User:
    """Thêm user mới; flush để CSDL cấp user.id (chưa commit)."""
    db.add(user)  # add chỉ đưa object vào session (chưa có I/O) nên không cần await
    await db.flush()  # await: chờ SQLite chạy INSERT và trả id
    return user


async def delete(db: AsyncSession, user: User) -> None:
    """Xóa user; các REVIEW của user tự xóa theo ON DELETE CASCADE."""
    await db.delete(user)
    await db.flush()
