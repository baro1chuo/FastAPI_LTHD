"""Tầng service – lưu ảnh tải lên (multipart/form-data) cho avatar người dùng và ảnh động vật.

Chỉ nhận ảnh JPEG/PNG/WEBP/GIF, tối đa MAX_IMAGE_BYTES; tên file sinh ngẫu nhiên (uuid) để không ghi đè
và không dùng tên do client đặt (tránh tên chứa "../" ghi ra ngoài thư mục).
"""
import uuid

from fastapi import UploadFile

from app.core import config
from app.core.exceptions import BusinessRuleError

# content_type được chấp nhận -> phần mở rộng file và "chữ ký" (magic bytes) ở đầu file thật
_ALLOWED = {
    "image/jpeg": (".jpg", (b"\xff\xd8\xff",)),
    "image/png": (".png", (b"\x89PNG\r\n\x1a\n",)),
    "image/gif": (".gif", (b"GIF87a", b"GIF89a")),
    "image/webp": (".webp", (b"RIFF",)),
}


async def save_image(upload: UploadFile, folder: str) -> str:
    """Kiểm tra rồi lưu ảnh vào app/static/uploads/<folder>/.

    Tham số: upload – file client gửi; folder – thư mục con ('avatars' hoặc 'animals').
    Trả về: đường dẫn công khai, vd "/static/uploads/animals/3f2a....jpg" (ghi vào cột image/avatar).
    Lỗi: BusinessRuleError (400) – không phải ảnh hợp lệ hoặc vượt dung lượng (UC08 E1, UC11 E1).
    """
    if upload.content_type not in _ALLOWED:
        raise BusinessRuleError("Chỉ nhận ảnh JPEG, PNG, WEBP hoặc GIF")
    ext, signatures = _ALLOWED[upload.content_type]
    # await: chờ đọc dữ liệu file từ request. Đọc tối đa MAX+1 byte: đủ biết file có vượt giới hạn không
    # mà không đọc hết file quá lớn vào RAM
    data = await upload.read(config.MAX_IMAGE_BYTES + 1)
    if len(data) > config.MAX_IMAGE_BYTES:
        raise BusinessRuleError(f"Ảnh vượt quá {config.MAX_IMAGE_BYTES // (1024 * 1024)} MB")
    # content_type do client tự khai nên có thể giả; kiểm tra thêm chữ ký ở đầu file thật
    # (WEBP bắt đầu bằng "RIFF" giống file âm thanh WAV nên kiểm thêm chữ "WEBP" ở byte 8–12)
    if not data.startswith(signatures) or (ext == ".webp" and data[8:12] != b"WEBP"):
        raise BusinessRuleError("File không phải ảnh hợp lệ")

    target_dir = config.UPLOAD_DIR / folder
    target_dir.mkdir(parents=True, exist_ok=True)
    filename = f"{uuid.uuid4().hex}{ext}"
    (target_dir / filename).write_bytes(data)
    return f"/static/uploads/{folder}/{filename}"
