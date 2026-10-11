from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.___.database import get_db
from app.___.deps import get_current_user
from app.routers import not_implemented
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse
from app.schemas.user import UserOut

router = APIRouter(prefix="/api/auth", tags=["Auth"])

@router.post("/register", response_model=UserOut, status_code=status.HTTP_201_CREATED)
def register(
    data: RegisterRequest,
    db: Session = Depends(get_db)
): 
    # TODO: user_service.create_user(db, data) -> 409 neu trung email
    not_implemented("user_service.create_user")

@router.post("/login", response_model=TokenResponse)
def login(data: LoginRequest, db: Session = Depends(get_db)):
# TODO: kiem tra mat khau (bcrypt), chan tai khoan bi khoa, tra JWT
    not_implemented("security.verify_password + security.create_access_token")

@router.get("/me", response_model=UserOut)
def me(current_user = Depends(get_current_user)):
    return current_user