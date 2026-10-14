from pydantic import BaseModel, ConfigDict
# - File này sẽ chứa các schema dùng cho:
# + animal: các thông tin cơ bản của các loài động vật

# + animal_translation: các bản dịch về thông tin của các loài động vật

# + AnimalWithTranslation: các thông tin cơ bản kèm bản dịch của động vật. 
# Đây là lớp hỗn hợp(nested class). Lớp này mới là dữ liệu trả về cho FE

# ===== ANIMAL =====

# Lớp cơ sở 
class AnimalBase(BaseModel):
    scientific_name: str
    zone_id: int
    category_id: int
    conservation_status_code: str
    popularity: int = 0 # mặc định là 0 khi tạo mới bên csdl
    featured: bool = False # Do trong csdl mặc định khi tạo mới là False nên để cho giống nhau
    image: str | None = None # Theo mặc định bên csdl giống bên trên

# ----- INPUT -----
# Lớp AnimalCreate và AnimalUpdate sẽ được sử dụng chung cho 2 trường hợp: gửi url và gửi file.
# Tạm thời sẽ làm trường hợp gửi url trước

# Lớp dùng để tạo animal mới
class AnimalCreate(AnimalBase):
    pass # cái này nghĩa là lớp con kế thừa hết, không thêm gì mới


# Lớp dùng để cập nhật animal
# Tất cả các trường đều là tùy chọn nên không kế thừa AnimalBase. Dùng cho PATCH
class AnimalUpdate(BaseModel):
    scientific_name: str | None = None
    zone_id: int | None = None
    category_id: int | None = None
    conservation_status_code: str | None = None
    featured: bool | None = None
    image: str | None = None


# ----- OUTPUT -----

# Lớp dùng để trả về thông tin của animal cho FE
class AnimalResponse(AnimalBase):
    id: int # Thêm ID 

    model_config = ConfigDict(from_attributes=True)



# ===== ANIMAL_TRANSLATION =====

# Lớp cơ sở
class AnimalTranslationBase(BaseModel):
    name: str
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


# Lớp dùng để cập nhật bản dịch animal
class AnimalTranslationUpdate(BaseModel):
    name: str | None = None
    appearance: str | None = None
    distribution: str | None = None
    ecology: str | None = None
    behaviour: str | None = None
    diet: str | None = None
    reproduction: str | None = None
    lifespan: str | None = None
    ecological_role: str | None = None
    threat: str | None = None



# ----- OUTPUT -----

# Lớp trả về kết quả cho FE
class AnimalTranslationResponse(AnimalTranslationBase):
    animal_id: int
    lang: str



# ===== ANIMAL WITH TRANSLATION =====

# Lớp này dùng để trả dữ liệu về cho FE
class AnimalWithTranslationResponse(
    AnimalBase,
    AnimalTranslationBase
):
    id: int # ID này là của bảng animal
    lang: str

    model_config = ConfigDict(from_attributes=True) 
    # cái này để pydantic đọc trực tiếp object từ SQLAlchemy