from fastapi import APIRouter, Depends 
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.deps import require_admin
from app.routers import not_implemented
from app.schema.animal import (
    AnimalCreate,
    AnimalDetail,
    AnimalListItem,
    AnimalUpdate,
)


router = APIRouter(prefix="/api/animals", tags=["Animals"])
#-----Guest-----
@router.get("", response_model=)
def list_animal():

@router.get("/{animal_id}", response_model=)
def get_animal():

@router.get("/{animal_id}/related", response_model=)
def get_related_animal():

#-----Admin-----
@router.post("", response_model=)
def create_animal():


@router.put("", response_model=)
def update_animal():

@router.delete("/{animal_id}", response_model=)
def delete_animal():

