"""Tầng core – kết nối SQLite: engine, SessionLocal, get_db() cho Depends, init_db() nạp dữ liệu mặc định.

Cấu trúc bảng KHÔNG tạo ở đây mà do Alembic quản lý (chạy "alembic upgrade head" trước khi chạy app).
"""
from sqlalchemy import create_engine, event
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import sessionmaker

from app.core import config

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
    """Chạy lúc khởi động app: thêm dữ liệu mặc định còn thiếu (ngôn ngữ, vai trò, cài đặt...).

    Bảng phải được tạo trước bằng "alembic upgrade head"; chưa có bảng -> RuntimeError kèm hướng dẫn.
    """
    from app.core.seed import seed  # import trong hàm để tránh vòng import khi load module

    try:
        with SessionLocal() as db:
            seed(db)
    except OperationalError as exc:  # thường là "no such table": CSDL mới chưa chạy migration
        raise RuntimeError("CSDL chưa có bảng. Hãy chạy: alembic upgrade head") from exc
