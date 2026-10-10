from fastapi import APIRouter, Depends, status
from sqlalchemy.orm import Session

from app.___.database import get_db #Thay doi sau
from app.___.deps import get_current_user, require_admin #lay nguoi dung hien tai ,yeu cau admin tu ben depend
from app.routers import not_implemented # not_implemented duoc hieu là chuc nang chua lam, 
from app.schemas.user import UserAdminUpdate, UserOut, UserUpdateMe #day la schema fake sau nay sua lai sau

router = APIRouter(
    prefix="/api/users",
    tags=["Users"],
)

# -----DOI VOI NGUOI DUNG DA DANG NHAP-----
@router.put("/update/me", response_model=UserOut) #Cap nhat tai khoan ca nhan
def update_me(
    data: UserUpdateMe,
    db: Session = Depends(get_db), 
    current_user: Depends = (get_current_user)           
):
    # TODO: doi thanh user_service.update_profile(db, current_user, data)
    not_implemented("user_service.update_profile")


# -----DOI VOI ADMIN-----
@router.get("", response_model=list[UserOut]) #Xem danh sach
def list_users(
    db: Session = Depends(get_db),
    admin = Depends(require_admin)
):
     # TODO: doi thanh user_service.list_users(db)
    not_implemented("user_service.list_users")



@router.get("/{user_id}", response_model=UserOut) #Tim 1 user (CAI NAY CHUA CO TRONG DAC TA API)
def get_user(
    user_id: int,
    db: Session = Depends(get_db),
    admin = Depends(require_admin)
):
     # TODO: doi thanh user_service.get_user(db)
    not_implemented("user_service.get_user")   



@router.patch("/{user_id}", response_model=UserOut) #Cap nhat tai khoan 
def update_user(
    user_id: int,
    data: UserAdminUpdate,
    db: Session = Depends(get_db),
    admin = Depends(require_admin)
):
     # TODO: user_service.set_status(db, admin, user_id, data) -> khong cho admin tu khoa tai khoan minh (400)
         not_implemented("user_service.set_status")



@router.delete("/{user_id}", status_code=status.HTTP_204_NO_CONTENT) #Xoa tai khoan 
def list_users(
    user_id: int,
    db: Session = Depends(get_db),
    admin = Depends(require_admin)
):
     # TODO: user_service.delete_user(db, admin, user_id)
    #       -> 400 neu admin tu xoa chinh , 404 neu khong co user
    not_implemented("user_service.delete_user")