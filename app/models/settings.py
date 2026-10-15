from sqlalchemy import Boolean, CheckConstraint, ForeignKey, Integer, String, text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.base import Base


class SystemSettings(Base):
    """Cài đặt hệ thống – bảng chỉ có đúng 1 dòng (id = 1)."""

    __tablename__ = "system_settings"
    __table_args__ = (CheckConstraint("id = 1", name="ck_system_settings_single_row"),)

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    zoo_name: Mapped[str] = mapped_column("zooName", String(100), nullable=False)
    open_hours: Mapped[str | None] = mapped_column("openHours", String(50))
    hotline: Mapped[str | None] = mapped_column(String(20))
    auto_approve: Mapped[bool] = mapped_column(
        "autoApprove", Boolean, nullable=False, server_default=text("0")
    )
    default_lang: Mapped[str] = mapped_column(
        "defaultLang", String(10), ForeignKey("language.code", ondelete="RESTRICT"), nullable=False
    )
