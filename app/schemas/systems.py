"""Tầng schema – dữ liệu vào/ra của nhóm API SYSTEMS: thống kê (UC15) và cài đặt hệ thống (UC16)."""
from pydantic import BaseModel, ConfigDict, Field, model_validator

# Giờ mở cửa dạng "07h00-17h00" (giờ 00–23, phút 00–59) – cùng định dạng cột openHours của bảng zone
OPEN_HOURS_PATTERN = r"^([01]\d|2[0-3])h[0-5]\d-([01]\d|2[0-3])h[0-5]\d$"
# Hotline: 8–20 ký tự gồm số, dấu cách, chấm, gạch ngang, có thể bắt đầu bằng +
HOTLINE_PATTERN = r"^\+?[0-9][0-9 .-]{6,18}[0-9]$"


# ----- OUTPUT -----

# Số đánh giá theo từng trạng thái
class ReviewCountByStatus(BaseModel):
    pending: int = 0
    approved: int = 0
    hidden: int = 0


# UC15 – số liệu tổng quan
class DashboardOut(BaseModel):
    total_animals: int # gồm cả động vật đang ẩn
    total_zones: int
    total_users: int
    total_reviews: int
    reviews_by_status: ReviewCountByStatus


# UC16 – cài đặt hiện tại (tên field trùng thuộc tính model SystemSettings để đọc thẳng từ ORM)
class SettingsOut(BaseModel):
    zoo_name: str
    open_hours: str | None
    hotline: str | None
    auto_approve: bool # tự duyệt đánh giá mới
    default_lang: str # ngôn ngữ dùng khi thiếu bản dịch

    model_config = ConfigDict(from_attributes=True)


# ----- INPUT -----

# UC16 – cập nhật cài đặt: chỉ field được gửi mới đổi
# Kiểm tra định dạng ở đây (sai -> 422); kiểm tra cần tra CSDL (ngôn ngữ có tồn tại, đang bật) ở service
class SettingsUpdate(BaseModel):
    zoo_name: str | None = Field(None, min_length=1, max_length=100)
    open_hours: str | None = Field(None, pattern=OPEN_HOURS_PATTERN, examples=["07h00-17h00"])
    hotline: str | None = Field(None, pattern=HOTLINE_PATTERN, max_length=20, examples=["1900 1234"])
    auto_approve: bool | None = None
    default_lang: str | None = Field(None, min_length=2, max_length=10)

    @model_validator(mode="after")
    def _check(self):
        """UC16 E1: giờ mở cửa phải trước giờ đóng cửa; các field bắt buộc không được gửi null."""
        for field in self.model_fields_set & {"zoo_name", "auto_approve", "default_lang"}:
            if getattr(self, field) is None:
                raise ValueError(f"Trường '{field}' không được để null")
        if self.open_hours:
            # Định dạng cố định nên so sánh chuỗi "07h00" < "17h00" đúng như so sánh thời gian
            open_at, close_at = self.open_hours.split("-")
            if open_at >= close_at:
                raise ValueError("Giờ mở cửa phải trước giờ đóng cửa")
        return self
