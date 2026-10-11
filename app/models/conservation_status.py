from sqlalchemy import CheckConstraint, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class ConservationStatus(Base):
    __tablename__ = "conservation_status"
    __table_args__ = (
        CheckConstraint(
            "code IN ('EX', 'EW', 'CR', 'EN', 'VU', 'NT', 'LC', 'DD', 'NE')",
            name="ck_conservation_status_code",
        ),
        CheckConstraint(
            "color IS NULL OR (length(color) = 7 "
            "AND color GLOB '#[0-9A-Fa-f]*' "
            "AND substr(color, 2) NOT GLOB '*[^0-9A-Fa-f]*')",
            name="ck_conservation_status_color",
        ),
    )

    code: Mapped[str] = mapped_column(String(2), primary_key=True)
    color: Mapped[str | None] = mapped_column(String(7))


class ConservationStatusTranslation(Base):
    __tablename__ = "conservation_status_translation"

    status_code: Mapped[str] = mapped_column(
        "statusCode",
        String(2),
        ForeignKey("conservation_status.code", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    lang: Mapped[str] = mapped_column(
        String(10), ForeignKey("language.code", ondelete="RESTRICT"), primary_key=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)