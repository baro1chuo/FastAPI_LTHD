"""Tầng router – kiểm tra backend còn sống (/api/health). Không đụng CSDL."""
from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["Health"])


@router.get("/health")
def health() -> dict:
    """Công khai – trả {"status": "ok"} nếu server đang chạy (dùng khi kiểm tra triển khai)."""
    return {"status": "ok"}
