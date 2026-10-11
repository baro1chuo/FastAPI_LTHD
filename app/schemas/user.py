from pydantic import BaseModel, EmailStr

class UserOut(BaseModel):
    id: int
    full_name: str
    username: str
    email: EmailStr
    role: str #user/admin
    is_active: bool
    model_config = {"from_attribute": True}

class UserUpdateMe(BaseModel):
    username: str | None = None
    full_name: str | None = None
    password: str | None = None

class UserAdminUpdate(BaseModel):
    is_active: bool | None = None
    role: str | None = None

