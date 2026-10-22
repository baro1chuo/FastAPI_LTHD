"""Tầng model – bảng ANIMAL (thông tin chung) và ANIMAL_TRANSLATION (nội dung theo từng ngôn ngữ)."""
from sqlalchemy import (
    Boolean,
    CheckConstraint,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Animal(Base):
    __tablename__ = "animal"
    __table_args__ = (
        CheckConstraint("available IN (0, 1)", name="ck_animal_available"),
        CheckConstraint("popularity >= 0", name="ck_animal_popularity"),
        {"sqlite_autoincrement": True},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    scientific_name: Mapped[str] = mapped_column(
        "scientificName", String(150), nullable=False, unique=True
    )
    zone_id: Mapped[int] = mapped_column(
        "zoneId", Integer, ForeignKey("zone.id", ondelete="RESTRICT"), nullable=False
    )
    category_id: Mapped[int] = mapped_column(
        "categoryId", Integer, ForeignKey("category.id", ondelete="RESTRICT"), nullable=False
    )
    conservation_status_code: Mapped[str] = mapped_column(
        "conservationStatusCode",
        String(2),
        ForeignKey("conservation_status.code", ondelete="RESTRICT"),
        nullable=False,
    )
    # Trạng thái hiển thị: 1 = đang hiển thị cho khách, 0 = đang ẩn (xóa mềm, UC11).
    # Mặc định 1 để động vật mới thêm hiện ngay.
    available: Mapped[bool] = mapped_column(
        Boolean, nullable=False, server_default=text("1")
    )
    popularity: Mapped[int] = mapped_column(Integer, nullable=False, server_default=text("0"))
    image: Mapped[str | None] = mapped_column(Text, server_default=text("NULL"))


class AnimalTranslation(Base):
    __tablename__ = "animal_translation"
    __table_args__ = (UniqueConstraint("lang", "name", name="uq_animal_translation_lang_name"),)

    animal_id: Mapped[int] = mapped_column(
        "animalId",
        Integer,
        ForeignKey("animal.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    lang: Mapped[str] = mapped_column(
        String(10), ForeignKey("language.code", ondelete="RESTRICT"), primary_key=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    appearance: Mapped[str | None] = mapped_column(Text)
    distribution: Mapped[str | None] = mapped_column(Text)
    ecology: Mapped[str | None] = mapped_column(Text)
    behaviour: Mapped[str | None] = mapped_column(Text)
    diet: Mapped[str | None] = mapped_column(Text)
    reproduction: Mapped[str | None] = mapped_column(Text)
    lifespan: Mapped[str | None] = mapped_column(Text)
    ecological_role: Mapped[str | None] = mapped_column("ecologicalRole", Text)
    threat: Mapped[str | None] = mapped_column(Text)