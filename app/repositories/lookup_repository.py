"""Truy vấn các bảng tra cứu: LANGUAGE, CATEGORY, CONSERVATION_STATUS."""
from sqlalchemy.orm import Session

from app.models.category import Category
from app.models.conservation_status import ConservationStatus
from app.models.language import Language


def get_language(db: Session, code: str) -> Language | None:
    """Lấy ngôn ngữ theo mã (vi, en...); không có thì trả None."""
    return db.get(Language, code)


def category_exists(db: Session, category_id: int) -> bool:
    """Nhóm động vật có tồn tại không."""
    return db.get(Category, category_id) is not None


def status_exists(db: Session, code: str) -> bool:
    """Mức bảo tồn (EX, CR, LC...) có tồn tại không."""
    return db.get(ConservationStatus, code) is not None
