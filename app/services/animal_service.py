"""Nghiệp vụ động vật: UC01 Xem/tìm/lọc, UC02 Chi tiết, UC03 Liên quan, UC11 Quản lý động vật."""
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.models.animal import Animal, AnimalTranslation
from app.repositories import animal_repository, lookup_repository, zone_repository
from app.schemas.animals import AnimalBase, AnimalCreate, AnimalTranslationBase, AnimalUpdate
from app.services.i18n import default_lang, resolve_lang

# Các cột của bảng ANIMAL và ANIMAL_TRANSLATION, lấy từ schema để không phải gõ lại
_ANIMAL_FIELDS = tuple(AnimalBase.model_fields)
_TRANSLATION_FIELDS = tuple(AnimalTranslationBase.model_fields)


def _to_item(animal: Animal, tr: AnimalTranslation | None) -> dict:
    """Ghép animal + bản dịch thành 1 dòng AnimalListItem; chưa có bản dịch nào thì tên = tên khoa học."""
    return {
        "id": animal.id,
        "name": tr.name if tr else animal.scientific_name,
        "scientific_name": animal.scientific_name,
        "image": animal.image,
        "zone_id": animal.zone_id,
        "category_id": animal.category_id,
        "conservation_status_code": animal.conservation_status_code,
        "featured": animal.featured,
        "popularity": animal.popularity,
    }


def _get_or_404(db: Session, animal_id: int) -> Animal:
    """Lấy động vật theo id; không có -> NotFoundError 404."""
    animal = animal_repository.get_by_id(db, animal_id)
    if animal is None:
        raise NotFoundError("Không tìm thấy động vật")
    return animal


def search_animals(db: Session, q: str | None = None, category_id: int | None = None,
                   zone_id: int | None = None, featured: bool | None = None, sort: str = "name",
                   lang: str | None = None, page: int = 1, size: int = 20) -> dict:
    """UC01 – tìm theo tên, lọc nhóm/khu vực/nổi bật, sắp xếp, phân trang.

    Trả {items, total, page, size} (schema AnimalPage). Tên lấy theo lang, thiếu thì theo ngôn ngữ mặc định.
    """
    rows, total = animal_repository.list_animals(
        db, resolve_lang(db, lang), default_lang(db), search=q, category_id=category_id,
        zone_id=zone_id, featured=featured, sort=sort, offset=(page - 1) * size, limit=size)
    return {"items": [_to_item(a, tr) for a, tr in rows], "total": total, "page": page, "size": size}


def get_animal(db: Session, animal_id: int, lang: str | None = None) -> dict:
    """UC02 – chi tiết động vật kèm bản dịch (schema AnimalWithTranslationResponse).

    Thứ tự chọn bản dịch: ngôn ngữ yêu cầu -> ngôn ngữ mặc định -> bản dịch bất kỳ. Không có -> 404.
    """
    animal = _get_or_404(db, animal_id)
    lang = resolve_lang(db, lang)
    tr = (animal_repository.get_translation(db, animal_id, lang)
          or animal_repository.get_translation(db, animal_id, default_lang(db))
          or next(iter(animal_repository.list_translations(db, animal_id)), None))
    data = {field: getattr(animal, field) for field in _ANIMAL_FIELDS}
    data.update({field: getattr(tr, field) if tr else None for field in _TRANSLATION_FIELDS})
    data.update(id=animal.id, name=tr.name if tr else animal.scientific_name, lang=tr.lang if tr else lang)
    return data


def get_related(db: Session, animal_id: int, lang: str | None = None, limit: int = 6) -> list[dict]:
    """UC03 – động vật cùng nhóm hoặc cùng khu vực (cùng nhóm xếp trước), không gồm chính nó. 404 nếu không có."""
    animal = _get_or_404(db, animal_id)
    rows = animal_repository.list_related(db, animal, resolve_lang(db, lang), default_lang(db), limit)
    return [_to_item(a, tr) for a, tr in rows]


def _admin_view(db: Session, animal: Animal) -> dict:
    """Dữ liệu trả admin sau khi tạo/sửa: thông tin chung + mọi bản dịch (schema AnimalAdminResponse)."""
    data = {field: getattr(animal, field) for field in _ANIMAL_FIELDS}
    data.update(id=animal.id, translations=animal_repository.list_translations(db, animal.id))
    return data


def _validate(db: Session, data: AnimalCreate, exclude_id: int | None = None) -> None:
    """Kiểm tra chung khi thêm/sửa (UC11).

    Khu vực / nhóm / mức bảo tồn không tồn tại -> 404; ngôn ngữ bản dịch không có -> 400;
    trùng tên khoa học hoặc trùng tên trong cùng ngôn ngữ -> 409. exclude_id: id đang sửa.
    """
    if not zone_repository.exists(db, data.zone_id):
        raise NotFoundError("Khu vực không tồn tại")
    if not lookup_repository.category_exists(db, data.category_id):
        raise NotFoundError("Nhóm động vật không tồn tại")
    if not lookup_repository.status_exists(db, data.conservation_status_code):
        raise NotFoundError("Mức bảo tồn không tồn tại")
    if animal_repository.exists_scientific_name(db, data.scientific_name, exclude_id):
        raise ConflictError("Tên khoa học đã tồn tại")
    for tr in data.translations:
        if lookup_repository.get_language(db, tr.lang) is None:
            raise BusinessRuleError(f"Ngôn ngữ '{tr.lang}' không được hỗ trợ")
        if animal_repository.exists_name(db, tr.lang, tr.name, exclude_id):
            raise ConflictError(f"Tên '{tr.name}' đã tồn tại")


def _translations(data: AnimalCreate) -> list[AnimalTranslation]:
    """Đổi danh sách bản dịch trong request thành các object model."""
    return [AnimalTranslation(**tr.model_dump()) for tr in data.translations]


def create_animal(db: Session, data: AnimalCreate) -> dict:
    """UC11 – thêm động vật kèm bản dịch trong MỘT giao dịch (lỗi bất kỳ bước nào thì không lưu gì)."""
    _validate(db, data)
    animal = animal_repository.add(
        db, Animal(**data.model_dump(include=set(_ANIMAL_FIELDS))), _translations(data))
    db.commit()
    return _admin_view(db, animal)


def update_animal(db: Session, animal_id: int, data: AnimalUpdate) -> dict:
    """UC11 – PUT ghi đè toàn bộ thông tin và bản dịch (bản dịch không gửi lên sẽ bị xóa). 404 nếu không có."""
    animal = _get_or_404(db, animal_id)
    _validate(db, data, exclude_id=animal_id)
    for field, value in data.model_dump(include=set(_ANIMAL_FIELDS)).items():
        setattr(animal, field, value)
    animal_repository.replace_translations(db, animal_id, _translations(data))
    db.commit()
    return _admin_view(db, animal)


def delete_animal(db: Session, animal_id: int) -> None:
    """UC11 – xóa động vật; bản dịch và đánh giá tự xóa theo ON DELETE CASCADE. 404 nếu không có."""
    animal_repository.delete(db, _get_or_404(db, animal_id))
    db.commit()
