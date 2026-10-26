"""Tầng repository – bảng ZONE và ZONE_TRANSLATION (async). Chỉ đọc: khu vực được nạp sẵn (seed),
không có API thêm/sửa/xóa."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.zone import Zone, ZoneTranslation


async def exists(db: AsyncSession, zone_id: int) -> bool:
    """Khu vực có tồn tại không (animal_service dùng khi thêm/sửa động vật)."""
    return await db.get(Zone, zone_id) is not None


async def list_zones(db: AsyncSession, lang: str, default_lang: str) -> list[tuple[Zone, ZoneTranslation | None]]:
    """UC01 – mọi khu vực kèm bản dịch: ngôn ngữ đang chọn, thiếu thì ngôn ngữ mặc định.

    Trả về: list các cặp (zone, bản dịch hoặc None), sắp theo id.
    """
    tr = aliased(ZoneTranslation)
    tr_def = aliased(ZoneTranslation)
    # LEFT JOIN 2 bản dịch để khu vực thiếu bản dịch ngôn ngữ đang chọn vẫn hiện (dùng bản mặc định)
    rows = (await db.execute(
        select(Zone, tr, tr_def)
        .outerjoin(tr, (tr.zone_id == Zone.id) & (tr.lang == lang))
        .outerjoin(tr_def, (tr_def.zone_id == Zone.id) & (tr_def.lang == default_lang))
        .order_by(Zone.id)
    )).all()  # await: chờ SQLite trả các dòng
    return [(zone, t or t_def) for zone, t, t_def in rows]
