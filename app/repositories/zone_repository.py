"""Tầng repository – bảng ZONE và ZONE_TRANSLATION. Chỉ đọc: khu vực được nạp sẵn (seed), không có API thêm/sửa/xóa."""
from sqlalchemy import select
from sqlalchemy.orm import Session, aliased

from app.models.zone import Zone, ZoneTranslation


def exists(db: Session, zone_id: int) -> bool:
    """Khu vực có tồn tại không (animal_service dùng khi thêm/sửa động vật)."""
    return db.get(Zone, zone_id) is not None


def list_zones(db: Session, lang: str, default_lang: str) -> list[tuple[Zone, ZoneTranslation | None]]:
    """UC01 – mọi khu vực kèm bản dịch: ngôn ngữ đang chọn, thiếu thì ngôn ngữ mặc định.

    Trả về: list các cặp (zone, bản dịch hoặc None), sắp theo id.
    """
    tr = aliased(ZoneTranslation)
    tr_def = aliased(ZoneTranslation)
    # LEFT JOIN 2 bản dịch để khu vực thiếu bản dịch ngôn ngữ đang chọn vẫn hiện (dùng bản mặc định)
    rows = db.execute(
        select(Zone, tr, tr_def)
        .outerjoin(tr, (tr.zone_id == Zone.id) & (tr.lang == lang))
        .outerjoin(tr_def, (tr_def.zone_id == Zone.id) & (tr_def.lang == default_lang))
        .order_by(Zone.id)
    ).all()
    return [(zone, t or t_def) for zone, t, t_def in rows]
