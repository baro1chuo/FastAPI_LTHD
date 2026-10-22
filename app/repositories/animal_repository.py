"""Tầng repository – truy vấn bảng ANIMAL và ANIMAL_TRANSLATION.

Chỉ viết câu truy vấn; không kiểm tra quy tắc nghiệp vụ, không commit (service commit 1 lần cho cả giao dịch).
"""
from sqlalchemy import Select, case, func, or_, select
from sqlalchemy.orm import Session, aliased

from app.models.animal import Animal, AnimalTranslation


def _select_translated(lang: str, default_lang: str) -> tuple[Select, type, type, type]:
    """Câu SELECT động vật kèm 3 bản dịch (LEFT JOIN): ngôn ngữ đang chọn, ngôn ngữ mặc định, bản bất kỳ.

    Tham số: lang – ngôn ngữ client chọn; default_lang – ngôn ngữ mặc định trong cài đặt.
    Trả về: (câu select, alias bản dịch đang chọn, alias mặc định, alias bất kỳ).
    """
    tr = aliased(AnimalTranslation)
    tr_def = aliased(AnimalTranslation)
    tr_any = aliased(AnimalTranslation)
    # Bản dịch "bất kỳ" = ngôn ngữ có mã nhỏ nhất của động vật đó (dự phòng cuối cùng)
    any_lang = (select(func.min(AnimalTranslation.lang))
                .where(AnimalTranslation.animal_id == Animal.id).correlate(Animal).scalar_subquery())
    # LEFT JOIN (không phải JOIN thường) để động vật thiếu bản dịch ngôn ngữ đang chọn vẫn hiện,
    # khi đó dùng bản dịch mặc định, rồi tới bản bất kỳ (quy tắc UC02: thiếu bản dịch -> dùng mặc định)
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
                 sort: str = "name", include_hidden: bool = False,
                 offset: int = 0, limit: int = 20) -> tuple[list[tuple[Animal, AnimalTranslation | None]], int]:
    """UC01 – danh sách động vật đã lọc + phân trang.

    Tham số: search – tìm gần đúng theo tên hiển thị hoặc tên khoa học; category_id/zone_id – lọc;
    sort – 'name' (A-Z) | 'popular' | 'newest'; include_hidden – True: lấy cả động vật đang ẩn (admin).
    Trả về: (các cặp (animal, bản dịch), tổng số kết quả trước phân trang).
    """
    stmt, tr, tr_def, tr_any = _select_translated(lang, default_lang)
    display_name = func.coalesce(tr.name, tr_def.name, tr_any.name, Animal.scientific_name)
    if not include_hidden:
        stmt = stmt.where(Animal.available.is_(True))  # khách chỉ thấy động vật đang hiển thị
    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(or_(display_name.ilike(pattern), Animal.scientific_name.ilike(pattern)))
    if category_id is not None:
        stmt = stmt.where(Animal.category_id == category_id)
    if zone_id is not None:
        stmt = stmt.where(Animal.zone_id == zone_id)

    # Đếm tổng TRƯỚC khi cắt trang để FE tính được số trang
    total = db.scalar(select(func.count()).select_from(stmt.subquery()))
    order = {
        "popular": (Animal.popularity.desc(), Animal.id),
        "newest": (Animal.id.desc(),),
    }.get(sort, (display_name, Animal.id))
    rows = db.execute(stmt.order_by(*order).offset(offset).limit(limit)).all()
    return _pick(rows), total


def list_related(db: Session, animal: Animal, lang: str, default_lang: str,
                 limit: int = 6) -> list[tuple[Animal, AnimalTranslation | None]]:
    """UC03 – động vật cùng nhóm HOẶC cùng khu vực, đang hiển thị, trừ chính nó.

    Cùng nhóm xếp trước (quy tắc UC03), rồi theo độ phổ biến. Trả về các cặp (animal, bản dịch).
    """
    stmt, *_ = _select_translated(lang, default_lang)
    stmt = stmt.where(
        Animal.id != animal.id,
        Animal.available.is_(True),  # không gợi ý động vật đang ẩn
        or_(Animal.category_id == animal.category_id, Animal.zone_id == animal.zone_id),
    ).order_by(
        case((Animal.category_id == animal.category_id, 0), else_=1),
        Animal.popularity.desc(),
        Animal.id,
    ).limit(limit)
    return _pick(db.execute(stmt).all())


def get_by_id(db: Session, animal_id: int) -> Animal | None:
    """Lấy động vật theo id (kể cả đang ẩn – service quyết định ai được xem); không có -> None."""
    return db.get(Animal, animal_id)


def get_translation(db: Session, animal_id: int, lang: str) -> AnimalTranslation | None:
    """Bản dịch của một động vật theo ngôn ngữ (khóa chính animalId + lang); không có -> None."""
    return db.get(AnimalTranslation, (animal_id, lang))


def list_translations(db: Session, animal_id: int) -> list[AnimalTranslation]:
    """Mọi bản dịch của một động vật, sắp theo mã ngôn ngữ (admin dùng để xem/sửa)."""
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
    """Thêm động vật kèm bản dịch. Trả về animal đã có id."""
    db.add(animal)
    db.flush()  # flush (chưa commit) để CSDL cấp animal.id, cần cho khóa ngoại của bản dịch
    for tr in translations:
        tr.animal_id = animal.id
    db.add_all(translations)
    db.flush()
    return animal


def upsert_translations(db: Session, animal_id: int, translations: list[AnimalTranslation]) -> None:
    """Thêm hoặc thay thế bản dịch theo từng ngôn ngữ (PATCH); ngôn ngữ không gửi lên giữ nguyên."""
    for tr in translations:
        tr.animal_id = animal_id
        # merge: đã có bản dịch (animalId, lang) thì chép đè giá trị mới, chưa có thì thêm mới
        db.merge(tr)
    db.flush()


def delete(db: Session, animal: Animal) -> None:
    """Xóa vĩnh viễn động vật; bản dịch và đánh giá tự xóa theo ON DELETE CASCADE trong CSDL."""
    db.delete(animal)
    db.flush()
