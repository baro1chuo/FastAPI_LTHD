"""Tầng service – nhóm động vật (chỉ đọc, phục vụ bộ lọc UC01)."""
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import lookup_repository
from app.services.i18n import default_lang, resolve_lang


async def list_categories(db: AsyncSession, lang: str | None = None) -> list[dict]:
    """UC01 – danh sách nhóm động vật theo ngôn ngữ (thiếu bản dịch thì dùng mã nhóm làm tên).

    Trả về: list dict theo schema CategoryOut. Không ném lỗi.
    """
    rows = await lookup_repository.list_categories(db, await resolve_lang(db, lang), await default_lang(db))
    return [{"id": c.id, "code": c.code, "name": tr.name if tr else c.code} for c, tr in rows]
