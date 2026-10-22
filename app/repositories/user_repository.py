"""Truy vấn bảng USER và ROLE. Không chứa quy tắc nghiệp vụ, không commit (service commit)."""
from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from app.models.role import Role
from app.models.user import User


def get_by_id(db: Session, user_id: int) -> User | None:
    """Lấy user theo id (kèm role); không có thì trả None."""
    return db.get(User, user_id)


def get_by_email(db: Session, email: str) -> User | None:
    """Tìm user theo email (cột UNIQUE); email truyền vào đã chuẩn hóa chữ thường."""
    return db.scalar(select(User).where(User.email == email))


def get_role_by_id(db: Session, role_id: int) -> Role | None:
    """Lấy vai trò theo id; không có thì trả None."""
    return db.get(Role, role_id)


def get_role_by_code(db: Session, code: str) -> Role | None:
    """Lấy vai trò theo code: 'admin' | 'staff' | 'user'."""
    return db.scalar(select(Role).where(Role.code == code))


def list_users(db: Session, search: str | None = None, status: str | None = None,
               offset: int = 0, limit: int = 20) -> list[User]:
    """Danh sách user, mới tạo trước.

    search: tìm gần đúng theo họ tên hoặc email; status: 'active' | 'locked'; offset/limit: phân trang.
    """
    stmt = select(User)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(or_(User.full_name.ilike(pattern), User.email.ilike(pattern)))
    if status:
        stmt = stmt.where(User.status == status)
    return list(db.scalars(stmt.order_by(User.created_at.desc(), User.id.desc()).offset(offset).limit(limit)))


def add(db: Session, user: User) -> User:
    """Thêm user mới; flush để có user.id ngay, service tự commit."""
    db.add(user)
    db.flush()
    return user


def delete(db: Session, user: User) -> None:
    """Xóa user; các REVIEW của user tự xóa theo ON DELETE CASCADE."""
    db.delete(user)
    db.flush()
