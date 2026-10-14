from pydantic import BaseModel

# Trả về thông tin của zone theo ngôn ngữ đã chọn ỏ frontend
class ZoneOut(BaseModel):  #tra ve theo ngon ngu
    id: int
    name: str
    description: str | None = None
    image_url: str | None = None
    model_config = {"from_attributes": True}

# Admin dùng để tạo zone mới theo ngôn ngữ đã chọn ở frontend
class ZoneCreate(BaseModel):
    name: str
    description: str | None = None
    image_url: str | None = None
    lang: str

# Admin dùng để cập nhật thông tin của zone
# Chưa rõ ràng phần sửa bản dịch của role
class ZoneUpdate(BaseModel):
    name: str
    description: str | None = None
    image_url: str | None = None
