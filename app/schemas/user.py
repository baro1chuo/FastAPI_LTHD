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
# Lớp dùng để trả dữ liệu của user cho admin, kế thừa UserBase
class UserAdminResponse(UserBase):
    id: int
    role_id: int
    status: UserStatus
    created_at: datetime

    # Pydantic đọc hẳn SQLAlchemy model một cách trực tiếp
    model_config = ConfigDict(from_attributes=True)


# Lớp dùng để trả về dữ liệu của user cho user, kế thừa UserBase
class UserResponse(UserBase):
    id: int # id của người dùng

    model_config = ConfigDict(from_attributes=True)



# ----- INPUT -----
# Lớp dùng trong quá trình đăng ký user, kế thừa UseBase
class UserCreate(UserBase):
    password: SecretStr = Field(min_length=8) # mật khẩu tối thiểu 8 ký tự


# Lớp này chỉ để cập nhật mật khẩu cho cả user và admin
# Bao gồm mật khẩu cũ, mật khẩu mới và xác nhận mật khẩu mới, kiểu dữ liệu là SecretStr
class UserPasswordUpdate(BaseModel):
    current_password: SecretStr
    new_password: SecretStr = Field(min_length=8)
    confirm_password: SecretStr

    # đống này là để kiểm tra sau khi nhận dữ liệu từ request
    # Tạm thời sẽ trả về như thế này!
    @model_validator(mode="after")
    def passwords_match(self):
        if self.new_password.get_secret_value() != self.confirm_password.get_secret_value():
            raise ValueError("New passwords do not match")

        if self.current_password.get_secret_value() == self.new_password.get_secret_value():
            raise ValueError("New password must be different")

        return self


# Lớp dùng để user thông thường cập nhật profile (PUT /api/users/update/me)
# Lớp này không cần kế thừa UserBase do các field đều là tùy chọn!
# Email KHÔNG có ở đây vì email không được sửa.
class UserProfileUpdate(BaseModel):
    full_name: str | None = Field(None, min_length=1, max_length=100) # các field có "= None" là có thể thêm vào hoặc không trong json
    avatar: str | None = None # đường dẫn ảnh đại diện
    password: UserPasswordUpdate | None = None # gửi kèm nếu muốn đổi mật khẩu


# Lớp để admin khóa/mở khóa hoặc đổi vai trò của user, cũng không cần kế thừa UserBase
# id lấy từ đường dẫn /api/users/{user_id} nên không cần trong body
class UserStatusUpdate(BaseModel):
    status: UserStatus | None = None
    role_id: int | None = None
