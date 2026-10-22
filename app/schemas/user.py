"""Tầng schema – dữ liệu vào/ra của API người dùng và đăng ký (Pydantic kiểm tra kiểu, sai -> 422).

Mật khẩu dùng SecretStr để không bị in ra log; dữ liệu trả về KHÔNG bao giờ có mật khẩu/hash.
"""
from datetime import datetime
from enum import Enum

from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr, model_validator

# Lớp enum định nghĩa trạng thái của user
class UserStatus(str, Enum):
    ACTIVE = "active"
    LOCKED = "locked"


# Lớp cơ sở cho các lớp khác, không phải lớp nào cũng phải kế thừa lớp này
class UserBase(BaseModel):
    full_name: str = Field(min_length=1, max_length=100)
    email: EmailStr
    avatar: str | None = None


# ----- OUTPUT -----
# Lớp dùng để trả dữ liệu của user cho admin (UC14), kế thừa UserBase
class UserAdminResponse(UserBase):
    id: int
    role_id: int
    status: UserStatus
    created_at: datetime

    # Pydantic đọc hẳn SQLAlchemy model một cách trực tiếp
    model_config = ConfigDict(from_attributes=True)


# Lớp dùng để trả về hồ sơ của chính user (UC08), kế thừa UserBase
class UserResponse(UserBase):
    id: int # id của người dùng
    created_at: datetime # ngày tạo tài khoản (UC08 bước 2)

    model_config = ConfigDict(from_attributes=True)



# ----- INPUT -----
# Lớp dùng trong quá trình đăng ký user (UC06), kế thừa UserBase
class UserCreate(UserBase):
    password: SecretStr = Field(min_length=8) # mật khẩu tối thiểu 8 ký tự


# Lớp này chỉ để đổi mật khẩu (UC08 A1)
# Bao gồm mật khẩu cũ, mật khẩu mới và xác nhận mật khẩu mới, kiểu dữ liệu là SecretStr
class UserPasswordUpdate(BaseModel):
    current_password: SecretStr
    new_password: SecretStr = Field(min_length=8)
    confirm_password: SecretStr

    # Kiểm tra sau khi nhận dữ liệu từ request: sai -> 422
    @model_validator(mode="after")
    def passwords_match(self):
        if self.new_password.get_secret_value() != self.confirm_password.get_secret_value():
            raise ValueError("New passwords do not match")

        if self.current_password.get_secret_value() == self.new_password.get_secret_value():
            raise ValueError("New password must be different")

        return self


# Lớp dùng để user cập nhật hồ sơ của chính mình (PATCH /api/users/me, UC08)
# Chỉ field được gửi mới đổi. Email KHÔNG có ở đây vì email không được sửa (UC08).
class UserProfileUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=1, max_length=100)
    avatar: str | None = None # đường dẫn ảnh; gửi null để xóa ảnh; tải file thì dùng POST /api/users/{id}/image
    password: UserPasswordUpdate | None = None # gửi kèm nếu muốn đổi mật khẩu

    @model_validator(mode="after")
    def _no_null_name(self):
        """full_name gửi null -> 422 (cột bắt buộc)."""
        if "full_name" in self.model_fields_set and self.full_name is None:
            raise ValueError("full_name không được để null")
        return self


# Lớp để admin khóa / mở khóa tài khoản (PATCH /api/users/{id}/status, UC14)
# Không có đổi vai trò vì UC14 chỉ gồm khóa, mở khóa, xóa
class UserStatusUpdate(BaseModel):
    status: UserStatus
