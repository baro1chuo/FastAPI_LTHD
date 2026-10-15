"""Dữ liệu mặc định thêm lúc khởi động. Chỉ thêm bản ghi còn thiếu nên chạy lại nhiều lần vẫn an toàn."""
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core import config
from app.core.security import hash_password
from app.models.category import Category, CategoryTranslation
from app.models.conservation_status import ConservationStatus, ConservationStatusTranslation
from app.models.identity import Role, User
from app.models.language import Language
from app.models.settings import SystemSettings
from app.models.zone import Zone, ZoneTranslation

LANGUAGES = (("vi", "Tiếng Việt"), ("en", "English"))

ROLES = (("admin", "Quản trị viên"), ("staff", "Nhân viên"), ("user", "Người dùng"))

# (mã IUCN, màu, tên tiếng Việt, tên tiếng Anh)
CONSERVATION_STATUSES = (
    ("EX", "#000000", "Tuyệt chủng", "Extinct"),
    ("EW", "#542344", "Tuyệt chủng trong tự nhiên", "Extinct in the Wild"),
    ("CR", "#D81E05", "Cực kỳ nguy cấp", "Critically Endangered"),
    ("EN", "#FC7F3F", "Nguy cấp", "Endangered"),
    ("VU", "#F9E814", "Sắp nguy cấp", "Vulnerable"),
    ("NT", "#CCE226", "Sắp bị đe dọa", "Near Threatened"),
    ("LC", "#60C659", "Ít quan tâm", "Least Concern"),
    ("DD", "#D1D1C6", "Thiếu dữ liệu", "Data Deficient"),
    ("NE", "#FFFFFF", "Chưa đánh giá", "Not Evaluated"),
)

# (code, tên tiếng Việt, tên tiếng Anh)
CATEGORIES = (
    ("mammal", "Thú", "Mammals"),
    ("bird", "Chim", "Birds"),
    ("reptile", "Bò sát", "Reptiles"),
    ("amphibian", "Lưỡng cư", "Amphibians"),
    ("fish", "Cá", "Fish"),
    ("invertebrate", "Không xương sống", "Invertebrates"),
)


def seed(db: Session) -> None:
    """Thêm ngôn ngữ, vai trò, mức bảo tồn, nhóm động vật, cài đặt, khu mẫu và admin (nếu có biến môi trường)."""
    langs = set(db.scalars(select(Language.code)))
    db.add_all(Language(code=c, name=n) for c, n in LANGUAGES if c not in langs)

    roles = set(db.scalars(select(Role.code)))
    db.add_all(Role(code=c, name=n) for c, n in ROLES if c not in roles)

    statuses = set(db.scalars(select(ConservationStatus.code)))
    for code, color, vi, en in CONSERVATION_STATUSES:
        if code not in statuses:
            db.add(ConservationStatus(code=code, color=color))
            db.add_all([ConservationStatusTranslation(status_code=code, lang="vi", name=vi),
                        ConservationStatusTranslation(status_code=code, lang="en", name=en)])

    categories = set(db.scalars(select(Category.code)))
    for code, vi, en in CATEGORIES:
        if code not in categories:
            category = Category(code=code)
            db.add(category)
            db.flush()  # cần category.id cho bản dịch
            db.add_all([CategoryTranslation(category_id=category.id, lang="vi", name=vi),
                        CategoryTranslation(category_id=category.id, lang="en", name=en)])

    if db.get(SystemSettings, 1) is None:
        db.add(SystemSettings(id=1, zoo_name="ZooGuide", open_hours="07h00-17h00",
                              auto_approve=False, default_lang="vi"))

    # ponytail: 1 khu mẫu để thêm được động vật khi chưa có API khu vực; bỏ khi zone_service xong
    if db.scalar(select(Zone.id).limit(1)) is None:
        zone = Zone(color="#4CAF50", open_hours="07h00-17h00")
        db.add(zone)
        db.flush()
        db.add(ZoneTranslation(zone_id=zone.id, lang="vi", name="Khu mẫu"))
    db.flush()

    if config.ADMIN_EMAIL and config.ADMIN_PASSWORD:
        email = config.ADMIN_EMAIL.lower()
        if db.scalar(select(User).where(User.email == email)) is None:
            admin_role = db.scalar(select(Role).where(Role.code == "admin"))
            db.add(User(full_name="Admin", email=email, role_id=admin_role.id,
                        password_hash=hash_password(config.ADMIN_PASSWORD)))
    db.commit()
