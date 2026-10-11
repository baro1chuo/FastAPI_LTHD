from sqlalchemy import ForeignKey, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Category(Base):
    __tablename__ = "category"
    __table_args__ = ({"sqlite_autoincrement": True},)

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    code: Mapped[str] = mapped_column(String(50), nullable=False, unique=True)


class CategoryTranslation(Base):
    __tablename__ = "category_translation"
    __table_args__ = (UniqueConstraint("lang", "name", name="uq_category_translation_lang_name"),)

    category_id: Mapped[int] = mapped_column(
        "categoryId",
        Integer,
        ForeignKey("category.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    lang: Mapped[str] = mapped_column(
        String(10), ForeignKey("language.code", ondelete="RESTRICT"), primary_key=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)