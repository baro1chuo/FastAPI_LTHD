"""Tầng model – lớp cơ sở cho mọi model SQLAlchemy của ZooGuide."""
from sqlalchemy import MetaData
from sqlalchemy.orm import DeclarativeBase

# Quy tắc tự đặt tên cho ràng buộc chưa có name=. Cần cho Alembic + SQLite: khi sửa bảng
# ở chế độ batch, Alembic phải biết TÊN ràng buộc mới xóa/tạo lại được. CHECK không có trong
# quy tắc vì mọi CheckConstraint đều tự ghi name= (ck_...).
NAMING_CONVENTION = {
    "ix": "ix_%(table_name)s_%(column_0_name)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s",
}


class Base(DeclarativeBase):
    """Lớp cha của mọi model; giữ Base.metadata (danh sách bảng) để Alembic so sánh khi autogenerate."""

    metadata = MetaData(naming_convention=NAMING_CONVENTION)
