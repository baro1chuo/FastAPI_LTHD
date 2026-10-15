"""Truy vấn bảng ANIMAL và ANIMAL_TRANSLATION. Không chứa quy tắc nghiệp vụ, không commit."""
from sqlalchemy import Select, case, delete as sql_delete, func, or_, select
from sqlalchemy.orm import Session, aliased

from app.models.animal import Animal, AnimalTranslation


def _select_translated(lang: str, default_lang: str) -> tuple[Select, type, type, type]:
    """Câu SELECT động vật kèm 3 bản dịch (LEFT JOIN): ngôn ngữ đang chọn, ngôn ngữ mặc định, bản bất kỳ.

    Nhờ LEFT JOIN, động vật chưa có bản dịch ngôn ngữ đang chọn vẫn hiện (dùng bản dự phòng).
    Trả (câu select, alias đang chọn, alias mặc định, alias bất kỳ).
    """
    tr = aliased(AnimalTranslation)
    tr_def = aliased(AnimalTranslation)
    tr_any = aliased(AnimalTranslation)
    any_lang = (select(func.min(AnimalTranslation.lang))
                .where(AnimalTranslation.animal_id == Animal.id).correlate(Animal).scalar_subquery())
    stmt = (
        select(Animal, tr, tr_def, tr_any)
        .outerjoin(tr, (tr.animal_id == Animal.id) & (tr.lang == lang))
        .outerjoin(tr_def, (tr_def.animal_id == Animal.id) & (tr_def.lang == default_lang))
        .outerjoin(tr_any, (tr_any.animal_id == Animal.id) & (tr_any.lang == any_lang))
    )
    return stmt, tr, tr_def, tr_any


def _pick(rows) -> list[tuple[Animal, AnimalTranslation | None]]:
    """Mỗi dòng (animal, 3 bản dịch) -> (animal, bản dịch dùng được theo thứ tự ưu tiên)."""
    return [(animal, tr or tr_def or tr_any) for animal, tr, tr_def, tr_any in rows]


def list_animals(db: Session, lang: str, default_lang: str, search: str | None = None,
                 category_id: int | None = None, zone_id: int | None = None,
                 featured: bool | None = None, sort: str = "name",
                 offset: int = 0, limit: int = 20) -> tuple[list[tuple[Animal, AnimalTranslation | None]], int]:
    """Danh sách động vật đã lọc + phân trang. Trả (các cặp (animal, bản dịch), tổng số kết quả).

    search: tìm gần đúng theo tên (2 ngôn ngữ) hoặc tên khoa học.
    sort: 'name' (A-Z) | 'popular' (phổ biến nhất) | 'newest' (mới thêm).
    """
    stmt, tr, tr_def, tr_any = _select_translated(lang, default_lang)
    display_name = func.coalesce(tr.name, tr_def.name, tr_any.name, Animal.scientific_name)
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(or_(display_name.ilike(pattern), Animal.scientific_name.ilike(pattern)))
    if category_id is not None:
        stmt = stmt.where(Animal.category_id == category_id)
    if zone_id is not None:
        stmt = stmt.where(Animal.zone_id == zone_id)
    if featured is not None:
        stmt = stmt.where(Animal.featured == featured)

    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    order = {
        "popular": (Animal.popularity.desc(), Animal.id),
        "newest": (Animal.id.desc(),),
    }.get(sort, (display_name, Animal.id))
    rows = db.execute(stmt.order_by(*order).offset(offset).limit(limit)).all()
    return _pick(rows), total


def list_related(db: Session, animal: Animal, lang: str, default_lang: str,
                 limit: int = 6) -> list[tuple[Animal, AnimalTranslation | None]]:
    """Động vật cùng nhóm HOẶC cùng khu vực, trừ chính nó; cùng nhóm xếp trước, rồi theo độ phổ biến."""
    stmt, *_ = _select_translated(lang, default_lang)
    stmt = stmt.where(
        Animal.id != animal.id,
        or_(Animal.category_id == animal.category_id, Animal.zone_id == animal.zone_id),
    ).order_by(
        case((Animal.category_id == animal.category_id, 0), else_=1),
        Animal.popularity.desc(),
        Animal.id,
    ).limit(limit)
    return _pick(db.execute(stmt).all())


def get_by_id(db: Session, animal_id: int) -> Animal | None:
    """Lấy động vật theo id; không có thì trả None."""
    return db.get(Animal, animal_id)


def get_translation(db: Session, animal_id: int, lang: str) -> AnimalTranslation | None:
    """Lấy bản dịch của một động vật theo ngôn ngữ; không có thì trả None."""
    return db.get(AnimalTranslation, (animal_id, lang))


def list_translations(db: Session, animal_id: int) -> list[AnimalTranslation]:
    """Mọi bản dịch của một động vật (admin dùng để sửa)."""
    return list(db.scalars(
        select(AnimalTranslation).where(AnimalTranslation.animal_id == animal_id).order_by(AnimalTranslation.lang)
    ))


def exists_scientific_name(db: Session, name: str, exclude_id: int | None = None) -> bool:
    """Tên khoa học đã có ở động vật khác chưa (cột UNIQUE). exclude_id: bỏ qua chính nó khi sửa."""
    stmt = select(Animal.id).where(Animal.scientific_name == name)
    if exclude_id is not None:
        stmt = stmt.where(Animal.id != exclude_id)
    return db.scalar(stmt.limit(1)) is not None


def exists_name(db: Session, lang: str, name: str, exclude_id: int | None = None) -> bool:
    """Tên hiển thị đã có trong cùng ngôn ngữ chưa (UNIQUE(lang, name)). exclude_id: bỏ qua chính nó."""
    stmt = select(AnimalTranslation.animal_id).where(AnimalTranslation.lang == lang, AnimalTranslation.name == name)
    if exclude_id is not None:
        stmt = stmt.where(AnimalTranslation.animal_id != exclude_id)
    return db.scalar(stmt.limit(1)) is not None


def add(db: Session, animal: Animal, translations: list[AnimalTranslation]) -> Animal:
    """Thêm động vật kèm bản dịch; flush để có animal.id, service tự commit."""
    db.add(animal)
    db.flush()
    for tr in translations:
        tr.animal_id = animal.id
    db.add_all(translations)
    db.flush()
    return animal


def replace_translations(db: Session, animal_id: int, translations: list[AnimalTranslation]) -> None:
    """Xóa toàn bộ bản dịch cũ rồi thêm bản mới (dùng cho PUT ghi đè)."""
    db.execute(sql_delete(AnimalTranslation).where(AnimalTranslation.animal_id == animal_id))
    for tr in translations:
        tr.animal_id = animal_id
    db.add_all(translations)
    db.flush()


def delete(db: Session, animal: Animal) -> None:
    """Xóa động vật; bản dịch và đánh giá tự xóa theo ON DELETE CASCADE."""
    db.delete(animal)
    db.flush()
