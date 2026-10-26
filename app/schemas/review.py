"""Tầng schema – dữ liệu vào/ra của API đánh giá (Pydantic kiểm tra kiểu, sai -> 422).

user_id KHÔNG có trong dữ liệu vào: luôn lấy từ JWT (dependency get_current_user) để không ai giả danh người khác.
"""
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, Field, model_validator

# Lớp enum định nghĩa trạng thái của review
class ReviewStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    HIDDEN = "hidden"


# ----- INPUT -----

# UC12 – người dùng sửa đánh giá của chính mình (PATCH /api/reviews/me/{id})
# Chỉ field được gửi mới đổi; không đổi được động vật của đánh giá
class ReviewUpdate(BaseModel):
    rating: int | None = Field(default=None, ge=1, le=5)
    comment: str | None = Field(default=None, max_length=500) # gửi null để xóa nội dung

    @model_validator(mode="after")
    def _check(self):
        """Phải gửi ít nhất 1 field; rating không được null (cột bắt buộc) -> 422."""
        if not self.model_fields_set:
            raise ValueError("Cần gửi rating hoặc comment")
        if "rating" in self.model_fields_set and self.rating is None:
            raise ValueError("rating không được để null")
        return self


# Dùng lúc tạo review mới, không cần id,
class ReviewCreate(BaseModel):
    animal_id: int # đánh giá cho động vật nào
    rating: int = Field(ge=1, le=5) # phải có rating
    comment: str | None = Field(default=None, max_length=500)
    lang: str = "vi" # ngôn ngữ viết đánh giá; không hợp lệ thì dùng ngôn ngữ mặc định


# Admin duyệt (approved) / ẩn (hidden) / đưa về chờ duyệt (pending)
class ReviewStatusUpdate(BaseModel):
    status: ReviewStatus



# ----- OUTPUT -----

# Dùng để trả về review cho FE
class ReviewResponse(BaseModel):
    id: int
    animal_id: int
    animal_name: str # tên động vật theo ngôn ngữ đang chọn (UC10, UC13)
    user_id: int
    user_name: str # họ tên người viết (UC04 bước 3, UC13)
    rating: int
    comment: str | None
    status: ReviewStatus
    created_at: datetime
    lang: str


# Danh sách đánh giá có phân trang, kèm điểm trung bình (UC04)
class ReviewPage(BaseModel):
    items: list[ReviewResponse]
    total: int # tổng số đánh giá khớp bộ lọc
    average: float | None # điểm trung bình (làm tròn 1 chữ số), chưa có đánh giá thì null
