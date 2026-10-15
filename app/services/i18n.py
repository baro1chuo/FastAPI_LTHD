"""Hàm dùng chung: chọn ngôn ngữ hiển thị cho mọi service."""
from sqlalchemy.orm import Session

from app.repositories import lookup_repository, settings_repository


def default_lang(db: Session) -> str:
    """Ngôn ngữ mặc định trong SYSTEM_SETTINGS (UC16)."""
    return settings_repository.get(db).default_lang


def resolve_lang(db: Session, lang: str | None) -> str:
    """Trả ngôn ngữ client gửi nếu có trong bảng LANGUAGE và đang bật; ngược lại trả ngôn ngữ mặc định."""
    if lang:
        language = lookup_repository.get_language(db, lang)
        if language is not None and language.is_active:
            return lang
    return default_lang(db)
