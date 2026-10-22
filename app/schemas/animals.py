"""Tầng schema – dữ liệu vào/ra của API động vật (Pydantic kiểm tra kiểu, sai -> 422).

- animal: thông tin chung của loài (tên khoa học, khu vực, nhóm, mức bảo tồn, ẩn/hiện...)
- animal_translation: nội dung theo từng ngôn ngữ (tên, mô tả...)
- AnimalWithTranslation: thông tin chung + bản dịch 1 ngôn ngữ, là dữ liệu trả về cho FE
"""
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

# ===== ANIMAL =====

# Lớp cơ sở
class AnimalBase(BaseModel):
    scientific_name: str = Field(min_length=1, max_length=150)
    zone_id: int
    category_id: int
    conservation_status_code: str = Field(min_length=2, max_length=2) # EX, EW, CR, EN, VU, NT, LC, DD, NE
    popularity: int = Field(0, ge=0) # mặc định là 0 khi tạo mới bên csdl
    available: bool = True # true = đang hiển thị, false = đang ẩn (xóa mềm)
    image: str | None = None # đường dẫn ảnh


# ===== ANIMAL_TRANSLATION =====

# Lớp cơ sở
class AnimalTranslationBase(BaseModel):
    name: str = Field(min_length=1, max_length=100)
    appearance: str | None = None
    distribution: str | None = None
    ecology: str | None = None
    behaviour: str | None = None
    diet: str | None = None
    reproduction: str | None = None
    lifespan: str | None = None
    ecological_role: str | None = None
    threat: str | None = None

# ----- INPUT -----

# Lớp dùng để tạo(thêm) bản dịch cho animal
class AnimalTranslationCreate(AnimalTranslationBase):
    lang: str # thêm trường lang để biết bản dịch là ngôn ngữ nào


# ----- OUTPUT -----

# Lớp trả về kết quả cho FE
class AnimalTranslationResponse(AnimalTranslationBase):
    lang: str

    model_config = ConfigDict(from_attributes=True)


def _check_unique_lang(value: list[AnimalTranslationCreate] | None):
    """Mỗi ngôn ngữ chỉ được có 1 bản dịch trong cùng một request (trùng -> 422)."""
    if value:
        langs = [tr.lang for tr in value]
        if len(langs) != len(set(langs)):
            raise ValueError("Mỗi ngôn ngữ chỉ được có 1 bản dịch")
    return value


# ===== INPUT CỦA ADMIN =====
# Ảnh gửi dạng đường dẫn có sẵn; muốn tải file ảnh thì dùng POST /api/animals/{id}/image

# Lớp dùng để tạo animal mới (POST): thông tin chung + ít nhất 1 bản dịch
class AnimalCreate(AnimalBase):
    translations: list[AnimalTranslationCreate] = Field(min_length=1)

    _unique_lang = field_validator("translations")(_check_unique_lang)


# Lớp dùng cho PATCH /api/animals/{id}: SỬA MỘT PHẦN, field nào không gửi thì giữ nguyên
# (service dùng model_dump(exclude_unset=True) để chỉ lấy field client thật sự gửi).
# Ẩn/hiện động vật (xóa mềm): chỉ gửi {"available": false} hoặc {"available": true}.
# translations: mỗi bản dịch gửi lên THAY THẾ bản dịch cùng ngôn ngữ; ngôn ngữ không gửi giữ nguyên.
class AnimalUpdate(BaseModel):
    scientific_name: str | None = Field(None, min_length=1, max_length=150)
    zone_id: int | None = None
    category_id: int | None = None
    conservation_status_code: str | None = Field(None, min_length=2, max_length=2)
    popularity: int | None = Field(None, ge=0)
    available: bool | None = None
    image: str | None = None
    translations: list[AnimalTranslationCreate] | None = None

    _unique_lang = field_validator("translations")(_check_unique_lang)

    # Gửi null cho cột bắt buộc (vd {"zone_id": null}) -> 422 thay vì lỗi NOT NULL ở CSDL (500).
    # Chỉ image được phép null (xóa ảnh).
    @model_validator(mode="after")
    def _no_null_required(self):
        for field in self.model_fields_set - {"image"}:
            if getattr(self, field) is None:
                raise ValueError(f"Trường '{field}' không được để null")
        return self


# ===== OUTPUT =====

# Một dòng trong danh sách động vật (UC01, UC03)
class AnimalListItem(BaseModel):
    id: int
    name: str # tên theo ngôn ngữ đang chọn, thiếu bản dịch thì dùng ngôn ngữ mặc định
    scientific_name: str
    image: str | None = None
    zone_id: int
    category_id: int
    conservation_status_code: str
    available: bool # khách luôn thấy true; admin thấy cả false (động vật đang ẩn)
    popularity: int


# Danh sách có phân trang
class AnimalPage(BaseModel):
    items: list[AnimalListItem]
    total: int # tổng số kết quả (để FE tính số trang)
    page: int
    size: int


# Chi tiết động vật kèm bản dịch theo 1 ngôn ngữ (UC02)
class AnimalWithTranslationResponse(
    AnimalBase,
    AnimalTranslationBase
):
    id: int # ID này là của bảng animal
    lang: str # ngôn ngữ thực tế của bản dịch trả về


# Trả cho admin sau khi tạo/sửa: thông tin chung + TẤT CẢ bản dịch
class AnimalAdminResponse(AnimalBase):
    id: int
    translations: list[AnimalTranslationResponse]

    model_config = ConfigDict(from_attributes=True)
