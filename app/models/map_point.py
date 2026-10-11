from decimal import Decimal

from sqlalchemy import CheckConstraint, ForeignKey, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class MapPoint(Base):
    __tablename__ = "MAP_POINT"
    __table_args__ = (
        CheckConstraint("type <> 'animal' OR animalId IS NOT NULL", name="ck_map_point_animal"),
        {"sqlite_autoincrement": True},
    )

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)
    point_type: Mapped[str] = mapped_column("type", String(30), nullable=False)
    zone_id: Mapped[int | None] = mapped_column(
        "zoneId", Integer, ForeignKey("zone.id", ondelete="SET NULL")
    )
    animal_id: Mapped[int | None] = mapped_column(
        "animalId", Integer, ForeignKey("animal.id", ondelete="SET NULL")
    )
    icon: Mapped[str | None] = mapped_column(String(100))
    latitude: Mapped[Decimal] = mapped_column(Numeric(9, 4), nullable=False)
    longitude: Mapped[Decimal] = mapped_column(Numeric(9, 4), nullable=False)


class MapPointTranslation(Base):
    __tablename__ = "MAP_POINT_TRANSLATION"

    map_point_id: Mapped[int] = mapped_column(
        "mapPointId",
        Integer,
        ForeignKey("MAP_POINT.id", ondelete="CASCADE"),
        primary_key=True,
        nullable=False,
    )
    lang: Mapped[str] = mapped_column(
        String(10), ForeignKey("language.code", ondelete="RESTRICT"), primary_key=True
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)