"""Tầng core – kết nối SQLite BẤT ĐỒNG BỘ (driver aiosqlite): engine, SessionLocal, get_db() cho Depends,
init_db() nạp dữ liệu mặc định lúc khởi động.

Cấu trúc bảng KHÔNG tạo ở đây mà do Alembic quản lý (chạy "alembic upgrade head" trước khi chạy app).
"""
from sqlalchemy import event
from sqlalchemy.exc import OperationalError
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core import config

# Engine async: mỗi câu truy vấn được gửi đi rồi "await" chờ kết quả, trong lúc chờ event loop
# phục vụ request khác thay vì đứng yên (khác Session đồng bộ chặn cả luồng)
engine = create_async_engine(config.DATABASE_URL)

# expire_on_commit=False: sau commit vẫn đọc được thuộc tính object mà không phải truy vấn lại.
# Với async bắt buộc nên tắt, vì "tự truy vấn lại khi đọc thuộc tính" (lazy load) không chạy được
# ngoài await và sẽ ném lỗi MissingGreenlet.
SessionLocal = async_sessionmaker(engine, expire_on_commit=False)


@event.listens_for(engine.sync_engine, "connect")
def _enable_foreign_keys(dbapi_conn, _):
    """Bật khóa ngoại cho MỖI kết nối (SQLite mặc định tắt) để ON DELETE CASCADE/RESTRICT có hiệu lực.

    Sự kiện "connect" chỉ có trên engine đồng bộ bên trong (engine.sync_engine); kết nối aiosqlite
    ở đây dùng giao diện DBAPI nên chạy lệnh qua cursor.
    """
    cursor = dbapi_conn.cursor()
    cursor.execute("PRAGMA foreign_keys = ON")
    cursor.close()


async def get_db():
    """Dependency: mở một AsyncSession cho mỗi request và luôn đóng khi request kết thúc (kể cả khi lỗi)."""
    async with SessionLocal() as db:
        yield db


async def init_db() -> None:
    """Chạy lúc khởi động app: thêm dữ liệu mặc định còn thiếu (ngôn ngữ, vai trò, cài đặt...).

    Bảng phải được tạo trước bằng "alembic upgrade head"; chưa có bảng -> RuntimeError kèm hướng dẫn.
    """
    from app.core.seed import seed  # import trong hàm để tránh vòng import khi load module

    try:
        async with SessionLocal() as db:
            await seed(db)  # await: chờ các câu truy vấn/ghi dữ liệu mặc định xuống SQLite
    except OperationalError as exc:  # thường là "no such table": CSDL mới chưa chạy migration
        raise RuntimeError("CSDL chưa có bảng. Hãy chạy: alembic upgrade head") from exc
