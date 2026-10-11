from datetime import datetime

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Review(Base):
    __tablename__ = "REVIEW"
    __table_args__ = (
        CheckConstraint("rating BETWEEN 1 AND 5", name="ck_review_rating"),
        CheckConstraint("comment IS NULL OR length(comment) <= 500", name="ck_review_comment_length"),
        CheckConstraint(
            "status IN ('pending', 'approved', 'hidden')", name="ck_review_status"
        ),
        UniqueConstraint("animalId", "userId", name="uq_review_animal_user"),
        {"sqlite_autoincrement": True},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    animal_id: Mapped[int] = mapped_column(
        "animalId", Integer, ForeignKey("animal.id", ondelete="CASCADE"), nullable=False
    )
    user_id: Mapped[int] = mapped_column(
        "userId", Integer, ForeignKey("user.id", ondelete="CASCADE"), nullable=False
    )
    rating: Mapped[int] = mapped_column(Integer, nullable=False)
    comment: Mapped[str | None] = mapped_column(String(500))
    status: Mapped[str] = mapped_column(
        String(10), nullable=False, server_default=text("'pending'")
    )
    created_at: Mapped[datetime] = mapped_column(
        "createdAt", DateTime, nullable=False, server_default=text("CURRENT_TIMESTAMP")
    )
    lang: Mapped[str] = mapped_column(
        String(10), ForeignKey("language.code", ondelete="RESTRICT"), nullable=False
    )