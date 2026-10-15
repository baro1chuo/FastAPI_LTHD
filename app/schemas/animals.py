from pydantic import BaseModel, ConfigDict, Field, field_validator
# - File này sẽ chứa các schema dùng cho:
# + animal: các thông tin cơ bản của các loài động vật

# + animal_translation: các bản dịch về thông tin của các loài động vật

# + AnimalWithTranslation: các thông tin cơ bản kèm bản dịch của động vật.
# Đây là lớp hỗn hợp(nested class). Lớp này mới là dữ liệu trả về cho FE

# ===== ANIMAL =====

# Lớp cơ sở
class AnimalBase(BaseModel):
    scientific_name: str = Field(min_length=1, max_length=150)
    zone_id: int
    category_id: int
    conservation_status_code: str = Field(min_length=2, max_length=2) # EX, EW, CR, EN, VU, NT, LC, DD, NE
    popularity: int = Field(0, ge=0) # mặc định là 0 khi tạo mới bên csdl
    featured: bool = False # động vật nổi bật (hiện ở trang chủ)
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


# ===== INPUT CỦA ADMIN =====
# Tạm thời ảnh gửi dạng url (chưa upload file)

# Lớp dùng để tạo animal mới: thông tin chung + ít nhất 1 bản dịch
class AnimalCreate(AnimalBase):
    translations: list[AnimalTranslationCreate] = Field(min_length=1)

    # mỗi ngôn ngữ chỉ được có 1 bản dịch
    @field_validator("translations")
    @classmethod
    def unique_lang(cls, value: list[AnimalTranslationCreate]):
        langs = [tr.lang for tr in value]
        if len(langs) != len(set(langs)):
            raise ValueError("Mỗi ngôn ngữ chỉ được có 1 bản dịch")
        return value


# Lớp dùng cho PUT /api/animals/{id}: GHI ĐÈ toàn bộ nên cần đủ trường như lúc tạo
# Bản dịch nào không gửi lên sẽ bị xóa
class AnimalUpdate(AnimalCreate):
    pass # cái này nghĩa là lớp con kế thừa hết, không thêm gì mới


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
    featured: bool
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
