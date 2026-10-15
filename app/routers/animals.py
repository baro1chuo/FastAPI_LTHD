from typing import Literal

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_admin
from app.schemas.animals import (
    AnimalAdminResponse,
    AnimalCreate,
    AnimalListItem,
    AnimalPage,
    AnimalUpdate,
    AnimalWithTranslationResponse,
)
from app.services import animal_service

router = APIRouter(prefix="/api/animals", tags=["Animals"])

# --- Guest ---
@router.get("", response_model=AnimalPage)
def list_animals(
    q: str | None = Query(None, description="Tìm theo tên hoặc tên khoa học"),
    category_id: int | None = Query(None, description="Lọc theo nhóm"),
    zone_id: int | None = Query(None, description="Lọc theo khu vực"),
    featured: bool | None = Query(None, description="Chỉ lấy động vật nổi bật"),
    sort: Literal["name", "popular", "newest"] = Query("name", description="Sắp xếp"),
    lang: str = Query("vi"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """UC01 – danh sách động vật: tìm, lọc, sắp xếp, phân trang."""
    return animal_service.search_animals(db, q, category_id, zone_id, featured, sort, lang, page, size)


@router.get("/{animal_id}", response_model=AnimalWithTranslationResponse)
def get_animal(
    animal_id: int,
    lang: str = Query("vi"),
    db: Session = Depends(get_db),
):
    """UC02 – chi tiết động vật theo ngôn ngữ; 404 nếu không có."""
    return animal_service.get_animal(db, animal_id, lang)


@router.get("/{animal_id}/related", response_model=list[AnimalListItem])
def get_related_animals(
    animal_id: int,
    lang: str = Query("vi"),
    limit: int = Query(6, ge=1, le=20),
    db: Session = Depends(get_db),
):
    """UC03 – động vật liên quan (cùng nhóm hoặc cùng khu vực)."""
    return animal_service.get_related(db, animal_id, lang, limit)


# --- Admin ---
@router.post("", response_model=AnimalAdminResponse, status_code=status.HTTP_201_CREATED)
def create_animal(
    data: AnimalCreate,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """UC11 – thêm động vật kèm bản dịch. 404 khu vực/nhóm/mức bảo tồn sai, 409 trùng tên."""
    return animal_service.create_animal(db, data)


@router.put("/{animal_id}", response_model=AnimalAdminResponse)
def update_animal(
    animal_id: int,
    data: AnimalUpdate,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """UC11 – ghi đè toàn bộ thông tin và bản dịch của động vật."""
    return animal_service.update_animal(db, animal_id, data)


@router.delete("/{animal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_animal(
    animal_id: int,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    """UC11 – xóa động vật (kèm bản dịch và đánh giá)."""
    animal_service.delete_animal(db, animal_id)
