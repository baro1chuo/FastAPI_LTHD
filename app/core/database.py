"""Kết nối SQLite: engine, SessionLocal, get_db() cho Depends, init_db() tạo bảng lúc khởi động."""
from pathlib import Path

from sqlalchemy import create_engine, event
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
    """Tạo thư mục chứa file CSDL, tạo mọi bảng còn thiếu theo models/, rồi thêm dữ liệu mặc định."""
    # import trong hàm để đăng ký đủ model vào Base.metadata mà không vòng import khi load module
    from app.core.seed import seed
    from app.models import animal, category, conservation_status, identity, language, map_point, review, settings, zone  # noqa: F401
    from app.models.base import Base

    if config.DATABASE_URL.startswith("sqlite:///"):
        Path(config.DATABASE_URL.removeprefix("sqlite:///")).parent.mkdir(parents=True, exist_ok=True)
    Base.metadata.create_all(engine)
    with SessionLocal() as db:
        seed(db)
