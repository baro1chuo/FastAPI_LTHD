from fastapi import APIRouter, Depends 
from sqlalchemy.orm import Session

from app.___.database import get_db #Thay doi sau
from app.___.deps import require_admin #Yeu cau admin tu ben depend
from app.routers import not_implemented # not_implemented duoc hieu là chuc nang chua lam, 
from app.schemas.admin import DashboardOut, SettingsOut, SettingsUpdate #day la schema fake sau nay sua lai sau

router = APIRouter(
    prefix="/api/admin",
    tags=["Admin"],
    dependencies=[Depends(require_admin)] 
)

@router.get("/dashboard", response_model=DashboardOut)
def dashboard(db: Session = Depends(get_db)):
    not_implemented("stats_service.get_dashboard")
# sau nay xoa not_implemented doi thanh return stats_service.get_dashboard(db)

@router.get("/settings", response_model=SettingsOut)
def get_settings(db: Session = Depends(get_db)):
    not_implemented("settings: đọc bảng SETTINGS")
# sau nay xoa not_implemented doi thanh return stats_service.get_settings(db)

@router.put("/settings", response_model=SettingsOut)
def update_settings(data: SettingsUpdate,db: Session = Depends(get_db)):
    not_implemented("settings: cập nhật bảng SETTINGS")
# sau nay xoa not_implemented doi thanh return stats_service.update_settings(data, db)