from decimal import Decimal

from sqlalchemy import (
    CheckConstraint,
    ForeignKey,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class Zone(Base):
    __tablename__ = "zone"
    __table_args__ = (
        CheckConstraint(
            "color IS NULL OR (length(color) = 7 "
            "AND substr(color, 1, 1) = '#' "
            "AND substr(color, 2) NOT GLOB '*[^0-9A-Fa-f]*')",
            name="ck_zone_color",
        ),
        CheckConstraint(
            "openHours IS NULL OR (length(openHours) = 11 "
            "AND substr(openHours, 3, 1) = 'h' "
            "AND substr(openHours, 6, 1) = '-' "
            "AND substr(openHours, 9, 1) = 'h' "
            "AND substr(openHours, 1, 2) GLOB '[0-2][0-9]' "
            "AND CAST(substr(openHours, 1, 2) AS INTEGER) BETWEEN 0 AND 23 "
            "AND substr(openHours, 4, 2) GLOB '[0-5][0-9]' "
            "AND substr(openHours, 7, 2) GLOB '[0-2][0-9]' "
            "AND CAST(substr(openHours, 7, 2) AS INTEGER) BETWEEN 0 AND 23 "
            "AND substr(openHours, 10, 2) GLOB '[0-5][0-9]')",
            name="ck_zone_open_hours",
        ),
        {"sqlite_autoincrement": True},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    color: Mapped[str | None] = mapped_column(String(7))
    open_hours: Mapped[str | None] = mapped_column("openHours", String(50))
    area_m2: Mapped[Decimal | None] = mapped_column("areaM2", Numeric(10, 2))
    image: Mapped[str | None] = mapped_column(String(255))


class ZoneTranslation(Base):
    __tablename__ = "zone_translation"
    __table_args__ = (UniqueConstraint("lang", "name", name="uq_zone_translation_lang_name"),)

    zone_id: Mapped[int] = mapped_column(
        "zoneId",
        Integer,
        ForeignKey("zone.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    lang: Mapped[str] = mapped_column(
        String(10), ForeignKey("language.code", ondelete="RESTRICT"), primary_key=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)