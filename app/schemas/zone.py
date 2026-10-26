"""Tầng schema – dữ liệu ra của API khu vực (chỉ đọc; không còn API thêm/sửa/xóa khu vực)."""
from pydantic import BaseModel


# Một khu vực theo ngôn ngữ đã chọn (UC01: dùng làm bộ lọc theo khu vực)
class ZoneOut(BaseModel):
    id: int
    name: str
    description: str | None = None
    color: str | None = None # màu #RRGGBB để FE tô trên giao diện
    open_hours: str | None = None # dạng "07h00-17h00"
    area_m2: float | None = None
    image: str | None = None
