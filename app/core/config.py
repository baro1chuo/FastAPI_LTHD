"""Cấu hình đọc từ biến môi trường; có giá trị mặc định để chạy thử ở máy cá nhân."""
import os

# Đường dẫn CSDL SQLite (file tạo trong thư mục app/database/)
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite:///./app/database/zoo.db")

# Khóa ký JWT – BẮT BUỘC đổi khi triển khai thật (đặt biến môi trường SECRET_KEY)
SECRET_KEY = os.getenv("SECRET_KEY", "dev-secret-change-me-zooguide-nhom9-2026")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

# Tài khoản admin tạo sẵn lúc khởi động (bỏ trống thì không tạo)
ADMIN_EMAIL = os.getenv("ADMIN_EMAIL")
ADMIN_PASSWORD = os.getenv("ADMIN_PASSWORD")
