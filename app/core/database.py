"""Kết nối SQLite: engine, SessionLocal, get_db() cho Depends, init_db() tạo bảng lúc khởi động."""
from pathlib import Path

from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import Session, sessionmaker

from app.core import config
from app.core.security import hash_password
from app.models.identity import Role, User

# check_same_thread=False: FastAPI chạy hàm def trên nhiều thread, SQLite mặc định cấm
engine = create_engine(config.DATABASE_URL, connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(engine, expire_on_commit=False)


@event.listens_for(engine, "connect")
def _enable_foreign_keys(dbapi_conn, _):
    """Bật khóa ngoại cho MỖI kết nối (SQLite mặc định tắt) để ON DELETE CASCADE/RESTRICT có hiệu lực."""
    dbapi_conn.execute("PRAGMA foreign_keys = ON")


def get_db():
    """Dependency: mở một Session cho mỗi request và luôn đóng khi request kết thúc."""
    with SessionLocal() as db:
        yield db


def init_db() -> None:
    """Tạo bảng ROLE, USER (nếu chưa có), thêm 3 vai trò mặc định và tài khoản admin từ biến môi trường.

    ponytail: chỉ tạo bảng phần user; khi model các bảng khác ổn định thì đổi thành
    Base.metadata.create_all(engine) hoặc dùng docs/zooguide_schema.sql.
    """
    if config.DATABASE_URL.startswith("sqlite:///"):
        Path(config.DATABASE_URL.removeprefix("sqlite:///")).parent.mkdir(parents=True, exist_ok=True)
    Role.metadata.create_all(engine, tables=[Role.__table__, User.__table__])

    with SessionLocal() as db:
        existing = set(db.scalars(select(Role.code)))
        for code, name in (("admin", "Quản trị viên"), ("staff", "Nhân viên"), ("user", "Người dùng")):
            if code not in existing:
                db.add(Role(code=code, name=name))
        db.flush()

        if config.ADMIN_EMAIL and config.ADMIN_PASSWORD:
            email = config.ADMIN_EMAIL.lower()
            if db.scalar(select(User).where(User.email == email)) is None:
                admin_role = db.scalar(select(Role).where(Role.code == "admin"))
                db.add(User(full_name="Admin", email=email, role_id=admin_role.id,
                            password_hash=hash_password(config.ADMIN_PASSWORD)))
        db.commit()
