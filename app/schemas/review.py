
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, Field

# Các lớp sẽ không có kế thừa base do không cần thiết
# user_id sẽ được lấy ra từ một hàm dependency

# Lớp enum định nghĩa trạng thái của review
class ReviewStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    HIDDEN = "hidden"


# ----- INPUT -----

# Dùng để người dùng thông thường cập nhật review của chính mình
class ReviewUpdate(BaseModel):
    rating: int | None = Field(default=None, ge=1, le=5)
    comment: str | None = Field(default=None, max_length=500)
# Có thể cập nhật rating hoặc comment
# rating ở đây dùng default=None để nếu không chỉnh thì sẽ không đưa vào body


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
    user_id: int
    rating: int
    comment: str | None
    status: ReviewStatus
    created_at: datetime
    lang: str

    model_config = ConfigDict(from_attributes=True)


# Danh sách đánh giá có phân trang, kèm điểm trung bình (UC05)
class ReviewPage(BaseModel):
    items: list[ReviewResponse]
    total: int # tổng số đánh giá khớp bộ lọc
    average: float | None # điểm trung bình (làm tròn 1 chữ số), chưa có đánh giá thì null
