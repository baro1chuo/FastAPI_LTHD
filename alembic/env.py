"""Cấu hình Alembic (công cụ migration): quản lý cấu trúc bảng SQLite theo các model trong app/models.

Alembic so sánh Base.metadata (model Python) với CSDL thật để sinh file migration trong alembic/versions,
rồi "alembic upgrade head" chạy các file đó để tạo/sửa bảng. Thay cho Base.metadata.create_all.
"""
import asyncio
from logging.config import fileConfig

from sqlalchemy import pool
from sqlalchemy.engine import Connection
from sqlalchemy.ext.asyncio import async_engine_from_config

from alembic import context

from app.core.config import DATABASE_URL
# Import đủ các module model để mọi bảng được đăng ký vào Base.metadata;
# thiếu module nào thì autogenerate tưởng bảng đó bị xóa và sinh lệnh drop_table.
from app.models import (  # noqa: F401
    animal, category, conservation_status, language, map_point, review, role, settings, user, zone,
)
from app.models.base import Base

config = context.config

# Đọc cấu hình log trong alembic.ini
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# Lấy URL từ app/core/config.py để Alembic và app luôn dùng CHUNG một file CSDL.
# Mẫu async của Alembic cần driver bất đồng bộ, nên "sqlite:///" (app đang chạy đồng bộ)
# được đổi thành "sqlite+aiosqlite:///"; URL đã là aiosqlite (sau bước chuyển async) thì giữ nguyên.
_url = DATABASE_URL
if _url.startswith("sqlite:///"):
    _url = _url.replace("sqlite:///", "sqlite+aiosqlite:///", 1)
config.set_main_option("sqlalchemy.url", _url)

# Metadata của các model: Alembic so sánh với CSDL thật để autogenerate
target_metadata = Base.metadata


def run_migrations_offline() -> None:
    """Chế độ offline ("alembic upgrade head --sql"): chỉ in câu SQL ra màn hình, không kết nối CSDL."""
    context.configure(
        url=config.get_main_option("sqlalchemy.url"),
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        # SQLite không hỗ trợ ALTER COLUMN / DROP CONSTRAINT nên bật chế độ batch:
        # Alembic tạo bảng mới, chép dữ liệu sang, xóa bảng cũ rồi đổi tên.
        render_as_batch=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    """Chạy các migration trên một kết nối đã mở (được gọi từ bên trong run_sync)."""
    # render_as_batch=True: lý do như ở chế độ offline (SQLite cần batch mode)
    context.configure(connection=connection, target_metadata=target_metadata, render_as_batch=True)

    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Chế độ online: tạo async engine, mở kết nối rồi chạy migration."""
    connectable = async_engine_from_config(
        config.get_section(config.config_ini_section, {}),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,  # migration chạy 1 lần rồi thoát, không cần giữ pool kết nối
    )

    async with connectable.connect() as connection:
        # await: chờ SQLite chạy xong các lệnh migration. Lệnh của Alembic là hàm đồng bộ
        # nên phải bọc trong run_sync để chạy được trên kết nối async.
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()  # await: chờ đóng hết kết nối tới file CSDL


def run_migrations_online() -> None:
    """Điểm vào cho "alembic upgrade/downgrade/revision": chạy hàm async bằng asyncio.run."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
