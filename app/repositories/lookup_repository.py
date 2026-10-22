"""Tầng repository – các bảng tra cứu: LANGUAGE, CATEGORY (+ bản dịch), CONSERVATION_STATUS (async)."""
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import aliased

from app.models.category import Category, CategoryTranslation
from app.models.conservation_status import ConservationStatus
from app.models.language import Language


async def get_language(db: AsyncSession, code: str) -> Language | None:
    """Lấy ngôn ngữ theo mã (vi, en...); không có -> None."""
    return await db.get(Language, code)


async def category_exists(db: AsyncSession, category_id: int) -> bool:
    """Nhóm động vật có tồn tại không."""
    return await db.get(Category, category_id) is not None


async def status_exists(db: AsyncSession, code: str) -> bool:
    """Mức bảo tồn (EX, CR, LC...) có tồn tại không."""
    return await db.get(ConservationStatus, code) is not None


async def list_categories(db: AsyncSession, lang: str,
                          default_lang: str) -> list[tuple[Category, CategoryTranslation | None]]:
    """UC01 – mọi nhóm động vật kèm tên theo ngôn ngữ đang chọn, thiếu thì ngôn ngữ mặc định.

    Trả về: list các cặp (category, bản dịch hoặc None), sắp theo id.
    """
    tr = aliased(CategoryTranslation)
    tr_def = aliased(CategoryTranslation)
    # LEFT JOIN 2 bản dịch: thiếu bản dịch ngôn ngữ đang chọn thì dùng bản mặc định
    rows = (await db.execute(
        select(Category, tr, tr_def)
        .outerjoin(tr, (tr.category_id == Category.id) & (tr.lang == lang))
        .outerjoin(tr_def, (tr_def.category_id == Category.id) & (tr_def.lang == default_lang))
        .order_by(Category.id)
    )).all()  # await: chờ SQLite trả các dòng
    return [(category, t or t_def) for category, t, t_def in rows]
