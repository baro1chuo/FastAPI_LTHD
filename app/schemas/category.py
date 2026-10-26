"""Tầng schema – dữ liệu ra của API nhóm động vật (chỉ đọc)."""
from pydantic import BaseModel


# Một nhóm động vật theo ngôn ngữ đã chọn (UC01: dùng làm bộ lọc theo nhóm)
class CategoryOut(BaseModel):
    id: int
    code: str # mã cố định: mammal, bird, reptile...
    name: str # tên theo ngôn ngữ
