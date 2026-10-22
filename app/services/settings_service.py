"""Tầng service – UC16 Chỉnh cài đặt hệ thống (giờ mở cửa, hotline, ngôn ngữ mặc định, tự duyệt đánh giá)."""
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError
from app.models.settings import SystemSettings
from app.repositories import lookup_repository, settings_repository
from app.schemas.systems import SettingsUpdate


def get_settings(db: Session) -> SystemSettings:
    """UC16 bước 2 – xem cài đặt hiện tại. Trả về: object SystemSettings (schema SettingsOut)."""
    return settings_repository.get(db)


def update_settings(db: Session, data: SettingsUpdate) -> SystemSettings:
    """UC16 – cập nhật cài đặt; chỉ field được gửi mới đổi. Áp dụng ngay cho các thao tác sau đó.

    Bật auto_approve KHÔNG đổi các đánh giá đang chờ duyệt (chỉ áp cho đánh giá gửi sau).
    Lỗi: BusinessRuleError (400) – default_lang không tồn tại hoặc đang tắt (UC16 E1);
    422 – sai định dạng giờ mở cửa / hotline (Pydantic).
    """
    fields = data.model_dump(exclude_unset=True)  # chỉ field client gửi
    if "default_lang" in fields:
        # Kiểm tra cần tra CSDL nên đặt ở service: ngôn ngữ phải có trong bảng LANGUAGE và đang bật
        language = lookup_repository.get_language(db, fields["default_lang"])
        if language is None or not language.is_active:
            raise BusinessRuleError(f"Ngôn ngữ '{fields['default_lang']}' không được hỗ trợ")
    settings = settings_repository.get(db)
    for field, value in fields.items():
        setattr(settings, field, value)
    db.commit()
    return settings
