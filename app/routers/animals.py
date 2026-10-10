from fastapi import APIRouter, Depends 
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_admin
from app.routers import not_implemented
from app.schemas.animal import (
    AnimalCreate,
    AnimalDetail,
    AnimalListItem,
    AnimalUpdate,
)

router = APIRouter(prefix="/api/animals", tags=["Animals"])

# --- Guest ---
@router.get("", response_model=list[AnimalListItem])
def list_animals(
    q: str | None = Query(None, description="Tìm theo tên"),
    category_id: int | None = Query(None, description="Lọc theo nhóm"),
    zone_id: int | None = Query(None, description="Lọc theo khu vực"),
    lang: str = Query("vi"),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    # TODO: animal_service.search_animals(db, q, category_id, zone_id, lang, page, size)
    not_implemented("animal_service.search_animals")


@router.get("/{animal_id}", response_model=AnimalDetail)
def get_animal(
    animal_id: int,
    lang: str = Query("vi"),
    db: Session = Depends(get_db),
):
    # TODO: animal_service.get_animal(db, animal_id, lang) -> 404 nếu không có
    not_implemented("animal_service.get_animal")


@router.get("/{animal_id}/related", response_model=list[AnimalListItem])
def get_related_animals(
    animal_id: int,
    lang: str = Query("vi"),
    limit: int = Query(6, ge=1, le=20),
    db: Session = Depends(get_db),
):
    # TODO: animal_service.get_related(db, animal_id, lang, limit)
    not_implemented("animal_service.get_related")


# --- Admin ---
@router.post("", response_model=AnimalDetail, status_code=status.HTTP_201_CREATED)
def create_animal(
    data: AnimalCreate,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    not_implemented("animal_service.create_animal")


@router.put("/{animal_id}", response_model=AnimalDetail)
def update_animal(
    animal_id: int,
    data: AnimalUpdate,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    not_implemented("animal_service.update_animal")


@router.delete("/{animal_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_animal(
    animal_id: int,
    db: Session = Depends(get_db),
    admin=Depends(require_admin),
):
    # TODO: animal_service.delete_animal (xóa kèm đánh giá)
    not_implemented("animal_service.delete_animal")
    return Response(status_code=status.HTTP_204_NO_CONTENT)
