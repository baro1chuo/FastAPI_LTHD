from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Integer, String, Text, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.models.base import Base


class Role(Base):
    __tablename__ = "role"
    __table_args__ = (
        CheckConstraint("code IN ('admin', 'staff', 'user')", name="ck_role_code"),
        {"sqlite_autoincrement": True},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(Text, nullable=False, unique=True)
    name: Mapped[str] = mapped_column(String(50), nullable=False)


class User(Base):
    __tablename__ = "user"
    __table_args__ = (
        CheckConstraint("status IN ('active', 'locked')", name="ck_user_status"),
        {"sqlite_autoincrement": True},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    full_name: Mapped[str] = mapped_column("fullName", String(100), nullable=False)
    email: Mapped[str] = mapped_column(String(255), nullable=False, unique=True)
    password_hash: Mapped[str] = mapped_column("passwordHash", String(255), nullable=False)
    role_id: Mapped[int] = mapped_column(
        "roleId", Integer, ForeignKey("role.id", ondelete="RESTRICT"), nullable=False
    )
    status: Mapped[str] = mapped_column(
        Text, nullable=False, server_default=text("'active'")
    )
    created_at: Mapped[datetime] = mapped_column(
        "createdAt", DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    avatar: Mapped[str | None] = mapped_column(Text)

    # Nạp kèm vai trò (JOIN) để đọc user.role.code khi tạo JWT / phân quyền
    role: Mapped[Role] = relationship(lazy="joined")