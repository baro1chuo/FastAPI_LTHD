from enum import Enum
from pydantic import BaseModel, ConfigDict, EmailStr, Field, SecretStr, model_validator

# Lớp enum định nghĩa trạng thái của user
class UserStatus(str, Enum):
    ACTIVE = "active"
    LOCKED = "locked"


# Lớp cơ sở cho các lớp khác, không phải lớp nào cũng phải kế thừa lớp này
class UserBase(BaseModel):
    full_name: str
    username: str
    email: EmailStr
    avatar: str | None = None
    

# ----- OUTPUT -----
# Lớp dùng để trả dữ liệu của user cho admin, kế thừa UserBase
class UserAdminResponse(UserBase):
    id: int
    role_id: int
    status: str
    created_at: Datetime

    # Pydantic đọc hẳn SQLAlchemy model một cách trực tiếp
    model_config = ConfigDict(from_attributes=True)


# Lớp dùng để trả về dữ liệu của user cho user, kế thừa UserBase
class UserResponse(UserBase):
    pass

    model_config = ConfigDict(from_attributes=True)



# ----- INPUT -----
# Lớp dùng trong quá trình đăng ký user, kế thừa UseBase
class UserCreate(UserBase):
    password: str # thêm password


# Lớp dùng để user thông thường cập nhật profile
# Lớp này không cần kế thừa UserBase do các field đều là tùy chọn!
class UserProfileUpdate(BaseModel):
    full_name: str | None = None # các field có "= None" là có thể thêm vào hoặc không trong json
    email: EmailStr | None = None
    # trường này để thông báo cho BE biết người dùng có cập nhật avatar không
    avatar_update: bool | None = None


# Lớp để admin cập nhật trạng thái(status) của user, cũng không cần kế thừa UserBase
class UserStatusUpdate(BaseModel):
    id: int 
    status: UserStatus


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

        if self.current_password == self.new_password:
            raise ValueError("New password must be different")

        return self
