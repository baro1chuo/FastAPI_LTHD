"""Tầng repository – các bảng tra cứu: LANGUAGE, CATEGORY (+ bản dịch), CONSERVATION_STATUS."""
from sqlalchemy import select
from sqlalchemy.orm import Session, aliased

from app.models.category import Category, CategoryTranslation
from app.models.conservation_status import ConservationStatus
from app.models.language import Language


def get_language(db: Session, code: str) -> Language | None:
    """Lấy ngôn ngữ theo mã (vi, en...); không có -> None."""
    return db.get(Language, code)


def category_exists(db: Session, category_id: int) -> bool:
    """Nhóm động vật có tồn tại không."""
    return db.get(Category, category_id) is not None


def status_exists(db: Session, code: str) -> bool:
    """Mức bảo tồn (EX, CR, LC...) có tồn tại không."""
    return db.get(ConservationStatus, code) is not None


def list_categories(db: Session, lang: str, default_lang: str) -> list[tuple[Category, CategoryTranslation | None]]:
    """UC01 – mọi nhóm động vật kèm tên theo ngôn ngữ đang chọn, thiếu thì ngôn ngữ mặc định.

    Trả về: list các cặp (category, bản dịch hoặc None), sắp theo id.
    """
    tr = aliased(CategoryTranslation)
    tr_def = aliased(CategoryTranslation)
    rows = db.execute(
        select(Category, tr, tr_def)
        .outerjoin(tr, (tr.category_id == Category.id) & (tr.lang == lang))
        .outerjoin(tr_def, (tr_def.category_id == Category.id) & (tr_def.lang == default_lang))
        .order_by(Category.id)
    ).all()
    return [(category, t or t_def) for category, t, t_def in rows]
