from pydantic import BaseModel, EmailStr

# File này sẽ chứa các class dùng trong quá trình đăng nhập/xuất và xác thực người dùng


# ----- INPUT -----

# Người dùng gửi thông tin khi đăng nhập
class LoginRequest(BaseModel):
    email: EmailStr
    password: str


# Người dùng gửi token để xác thực bản thân
class AuthenticationRequest(BaseModel):
    token: str



# ----- OUTPUT -----

# Dùng để trả về JWT(JSON Web Token) sau khi đăng nhập thành công
class TokenResponse(BaseModel):
    token: str


# Lớp gửi kết quả xác thực về cho người dùng
class AuthenticationResponse(BaseModel):
    validation: bool
    description: str | None = None
