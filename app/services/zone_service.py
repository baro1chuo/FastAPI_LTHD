"""Tầng service – khu vực (chỉ đọc, phục vụ bộ lọc UC01). Khu vực được nạp sẵn nên không có thêm/sửa/xóa."""
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import zone_repository
from app.services.i18n import default_lang, resolve_lang


async def list_zones(db: AsyncSession, lang: str | None = None) -> list[dict]:
    """UC01 – danh sách khu vực theo ngôn ngữ (thiếu bản dịch thì dùng ngôn ngữ mặc định).

    Trả về: list dict theo schema ZoneOut. Không ném lỗi.
    """
    rows = await zone_repository.list_zones(db, await resolve_lang(db, lang), await default_lang(db))
    return [{
        "id": zone.id,
        "name": tr.name if tr else f"Khu {zone.id}",  # chưa có bản dịch nào: tên tạm theo id
        "description": tr.description if tr else None,
        "color": zone.color,
        "open_hours": zone.open_hours,
        "area_m2": float(zone.area_m2) if zone.area_m2 is not None else None,  # Decimal -> số cho JSON
        "image": zone.image,
    } for zone, tr in rows]
