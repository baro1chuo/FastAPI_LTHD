"""Tầng service – nghiệp vụ động vật: UC01 Xem/tìm/lọc, UC02 Chi tiết, UC03 Liên quan, UC11 Quản lý động vật.

Áp quy tắc nghiệp vụ (ẩn/hiện, trùng tên, tồn tại khóa ngoại), gọi repository, commit giao dịch.
"""
from fastapi import UploadFile
from sqlalchemy.orm import Session

from app.core.exceptions import BusinessRuleError, ConflictError, NotFoundError
from app.models.animal import Animal, AnimalTranslation
from app.repositories import animal_repository, lookup_repository, zone_repository
from app.schemas.animals import AnimalBase, AnimalCreate, AnimalTranslationBase, AnimalTranslationCreate, AnimalUpdate
from app.services import image_service
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
        "available": animal.available,
        "popularity": animal.popularity,
    }


def _get_or_404(db: Session, animal_id: int, include_hidden: bool = True) -> Animal:
    """Lấy động vật theo id.

    include_hidden=False: động vật đang ẩn coi như không tồn tại (khách không được biết nó còn trong CSDL).
    Lỗi: NotFoundError (404) nếu không có, hoặc đang ẩn mà include_hidden=False.
    """
    animal = animal_repository.get_by_id(db, animal_id)
    # Kiểm tra available: động vật đang ẩn trả 404 giống như đã xóa (UC02 E1, UC09 E3)
    if animal is None or (not include_hidden and not animal.available):
        raise NotFoundError("Không tìm thấy động vật")
    return animal


def get_visible_animal(db: Session, animal_id: int) -> Animal:
    """Lấy động vật ĐANG HIỂN THỊ (dùng cho service khác, vd review). Không có hoặc đang ẩn -> 404."""
    return _get_or_404(db, animal_id, include_hidden=False)


def search_animals(db: Session, q: str | None = None, category_id: int | None = None,
                   zone_id: int | None = None, sort: str = "name", lang: str | None = None,
                   page: int = 1, size: int = 20, include_hidden: bool = False) -> dict:
    """UC01 – Xem/tìm/lọc động vật.

    Tham số: q – từ khóa tên; category_id, zone_id – bộ lọc; sort – name|popular|newest;
    lang – ngôn ngữ hiển thị; page/size – phân trang; include_hidden – True khi người gọi là admin (UC11).
    Trả về: {items, total, page, size} (schema AnimalPage). Không ném lỗi (không có kết quả -> items rỗng).
    """
    rows, total = animal_repository.list_animals(
        db, resolve_lang(db, lang), default_lang(db), search=q, category_id=category_id,
        zone_id=zone_id, sort=sort, include_hidden=include_hidden,
        offset=(page - 1) * size, limit=size)  # phân trang: bỏ qua (page-1)*size dòng đầu
    return {"items": [_to_item(a, tr) for a, tr in rows], "total": total, "page": page, "size": size}


def get_animal(db: Session, animal_id: int, lang: str | None = None, include_hidden: bool = False) -> dict:
    """UC02 – Xem chi tiết động vật.

    Tham số: lang – ngôn ngữ hiển thị; include_hidden – True khi người gọi là admin.
    Trả về: dict theo schema AnimalWithTranslationResponse. Thứ tự chọn bản dịch:
    ngôn ngữ yêu cầu -> ngôn ngữ mặc định -> bản dịch bất kỳ.
    Lỗi: NotFoundError (404) nếu không có hoặc đang ẩn với khách.
    """
    animal = _get_or_404(db, animal_id, include_hidden)
    lang = resolve_lang(db, lang)
    tr = (animal_repository.get_translation(db, animal_id, lang)
          or animal_repository.get_translation(db, animal_id, default_lang(db))
          or next(iter(animal_repository.list_translations(db, animal_id)), None))
    data = {field: getattr(animal, field) for field in _ANIMAL_FIELDS}
    data.update({field: getattr(tr, field) if tr else None for field in _TRANSLATION_FIELDS})
    data.update(id=animal.id, name=tr.name if tr else animal.scientific_name, lang=tr.lang if tr else lang)
    return data


def get_related(db: Session, animal_id: int, lang: str | None = None, limit: int = 6) -> list[dict]:
    """UC03 – Xem động vật liên quan: cùng nhóm hoặc cùng khu vực, chỉ động vật đang hiển thị.

    Trả về: danh sách AnimalListItem (cùng nhóm xếp trước). Lỗi: 404 nếu động vật gốc không có hoặc đang ẩn.
    """
    animal = _get_or_404(db, animal_id, include_hidden=False)
    rows = animal_repository.list_related(db, animal, resolve_lang(db, lang), default_lang(db), limit)
    return [_to_item(a, tr) for a, tr in rows]


def _admin_view(db: Session, animal: Animal) -> dict:
    """Dữ liệu trả admin sau khi tạo/sửa: thông tin chung + mọi bản dịch (schema AnimalAdminResponse)."""
    data = {field: getattr(animal, field) for field in _ANIMAL_FIELDS}
    data.update(id=animal.id, translations=animal_repository.list_translations(db, animal.id))
    return data


def _validate(db: Session, fields: dict, translations: list[AnimalTranslationCreate],
              exclude_id: int | None = None) -> None:
    """Kiểm tra cần tra CSDL khi thêm/sửa (UC11 E1, E2). Chỉ kiểm tra field có trong `fields`.

    Lỗi: NotFoundError (404) – khu vực / nhóm / mức bảo tồn không tồn tại;
    BusinessRuleError (400) – ngôn ngữ bản dịch không được hỗ trợ;
    ConflictError (409) – trùng tên khoa học, hoặc trùng tên trong cùng ngôn ngữ.
    """
    if "zone_id" in fields and not zone_repository.exists(db, fields["zone_id"]):
        raise NotFoundError("Khu vực không tồn tại")
    if "category_id" in fields and not lookup_repository.category_exists(db, fields["category_id"]):
        raise NotFoundError("Nhóm động vật không tồn tại")
    if ("conservation_status_code" in fields
            and not lookup_repository.status_exists(db, fields["conservation_status_code"])):
        raise NotFoundError("Mức bảo tồn không tồn tại")
    # Kiểm tra trùng ở service để trả 409 dễ hiểu, thay vì để CSDL ném lỗi UNIQUE (500)
    if "scientific_name" in fields and animal_repository.exists_scientific_name(
            db, fields["scientific_name"], exclude_id):
        raise ConflictError("Tên khoa học đã tồn tại")
    for tr in translations:
        if lookup_repository.get_language(db, tr.lang) is None:
            raise BusinessRuleError(f"Ngôn ngữ '{tr.lang}' không được hỗ trợ")
        if animal_repository.exists_name(db, tr.lang, tr.name, exclude_id):
            raise ConflictError(f"Tên '{tr.name}' đã tồn tại")


def _translations(items: list[AnimalTranslationCreate]) -> list[AnimalTranslation]:
    """Đổi danh sách bản dịch trong request thành các object model."""
    return [AnimalTranslation(**tr.model_dump()) for tr in items]


def create_animal(db: Session, data: AnimalCreate) -> dict:
    """UC11 – Thêm động vật kèm bản dịch trong MỘT giao dịch.

    Trả về: AnimalAdminResponse (kèm mọi bản dịch). Lỗi: 404/400/409 như _validate; 422 do Pydantic.
    """
    fields = data.model_dump(include=set(_ANIMAL_FIELDS))
    _validate(db, fields, data.translations)
    animal = animal_repository.add(db, Animal(**fields), _translations(data.translations))
    # Commit ở service (không ở repository) để thêm động vật + bản dịch là 1 giao dịch:
    # lỗi ở bất kỳ bước nào thì không có gì được lưu
    db.commit()
    return _admin_view(db, animal)


def update_animal(db: Session, animal_id: int, data: AnimalUpdate) -> dict:
    """UC11 – Sửa một phần động vật (PATCH), gồm cả ẩn/hiện bằng available (xóa mềm, UC11 A2).

    Chỉ field client thật sự gửi mới được đổi (exclude_unset). Bản dịch gửi lên thay thế bản cùng ngôn ngữ.
    Trả về: AnimalAdminResponse. Lỗi: 404 nếu không có động vật; 404/400/409 như _validate.
    """
    animal = _get_or_404(db, animal_id)  # admin sửa được cả động vật đang ẩn
    # exclude_unset: chỉ lấy field có trong JSON gửi lên, để field không gửi giữ nguyên giá trị cũ
    fields = data.model_dump(exclude_unset=True, exclude={"translations"})
    translations = data.translations or []
    _validate(db, fields, translations, exclude_id=animal_id)
    for field, value in fields.items():
        setattr(animal, field, value)
    if translations:
        animal_repository.upsert_translations(db, animal_id, _translations(translations))
    db.commit()  # commit 1 lần cho cả thông tin chung và bản dịch
    return _admin_view(db, animal)


def upload_image(db: Session, animal_id: int, upload: UploadFile) -> dict:
    """UC11 – Tải ảnh động vật (multipart/form-data); lưu file rồi ghi đường dẫn vào cột image.

    Trả về: AnimalAdminResponse. Lỗi: 404 không có động vật; 400 không phải ảnh hợp lệ / vượt dung lượng.
    """
    animal = _get_or_404(db, animal_id)  # kiểm tra động vật trước để không lưu file "mồ côi"
    animal.image = image_service.save_image(upload, "animals")
    db.commit()
    return _admin_view(db, animal)


def delete_animal(db: Session, animal_id: int) -> None:
    """UC11 – Xóa vĩnh viễn động vật; bản dịch và đánh giá tự xóa theo ON DELETE CASCADE.

    TODO: chờ nhóm chốt giữ xóa thật hay rút về khung (muốn tạm ngừng hiển thị thì dùng PATCH available=false).
    Lỗi: NotFoundError (404) nếu không có.
    """
    animal_repository.delete(db, _get_or_404(db, animal_id))
    db.commit()
