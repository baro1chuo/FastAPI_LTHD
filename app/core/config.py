"""Tầng core – cấu hình đọc từ biến môi trường; có giá trị mặc định để chạy thử ở máy cá nhân."""
import os
from pathlib import Path

# Đường dẫn CSDL SQLite (file trong app/database/). "+aiosqlite" = driver bất đồng bộ để dùng async/await
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./app/database/zoo.db")

# Khóa ký JWT – BẮT BUỘC đổi khi triển khai thật (đặt biến môi trường SECRET_KEY)
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me-zooguide-nhom9-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

# Tài khoản admin tạo sẵn lúc khởi động (bỏ trống thì không tạo)
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")

# Ảnh tải lên: lưu trong app/static/uploads/, phục vụ ra ngoài qua đường dẫn /static/uploads/...
STATIC_DIR = Path(__file__).resolve().parent.parent / "static"
UPLOAD_DIR = STATIC_DIR / "uploads"
MAX_IMAGE_BYTES = int(os.getenv("MAX_IMAGE_BYTES", str(2 * 1024 * 1024)))  # mặc định tối đa 2 MB / ảnh
