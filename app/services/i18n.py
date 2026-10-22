"""Tầng service – hàm dùng chung: chọn ngôn ngữ hiển thị cho mọi service.

Frontend gửi lang (GET: ?lang=vi, POST/PATCH: trong body). Ngôn ngữ không có / đang tắt -> dùng defaultLang
trong SYSTEM_SETTINGS (UC16).
"""
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories import lookup_repository, settings_repository


async def default_lang(db: AsyncSession) -> str:
    """Ngôn ngữ mặc định trong SYSTEM_SETTINGS (UC16)."""
    return (await settings_repository.get(db)).default_lang  # await: chờ SQLite đọc dòng cài đặt


async def resolve_lang(db: AsyncSession, lang: str | None) -> str:
    """Trả ngôn ngữ client gửi nếu có trong bảng LANGUAGE và đang bật; ngược lại trả ngôn ngữ mặc định."""
    if lang:
        language = await lookup_repository.get_language(db, lang)
        if language is not None and language.is_active:
            return lang
    return await default_lang(db)
