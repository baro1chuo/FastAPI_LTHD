"""Tầng core – dữ liệu mặc định thêm lúc khởi động app. Chỉ thêm bản ghi còn thiếu nên chạy lại nhiều lần vẫn an toàn."""
from fastapi.concurrency import run_in_threadpool
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core import config
from app.core.security import hash_password
from app.models.category import Category, CategoryTranslation
from app.models.conservation_status import ConservationStatus, ConservationStatusTranslation
from app.models.role import Role
from app.models.user import User
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


async def seed(db: AsyncSession) -> None:
    """Thêm ngôn ngữ, vai trò, mức bảo tồn, nhóm động vật, cài đặt, khu mẫu và admin (nếu có biến môi trường).

    Mỗi "await db.scalars/get/flush" là chờ SQLite trả kết quả; commit 1 lần ở cuối cho cả giao dịch.
    """
    langs = set(await db.scalars(select(Language.code)))
    db.add_all(Language(code=c, name=n) for c, n in LANGUAGES if c not in langs)

    roles = set(await db.scalars(select(Role.code)))
    db.add_all(Role(code=c, name=n) for c, n in ROLES if c not in roles)

    statuses = set(await db.scalars(select(ConservationStatus.code)))
    for code, color, vi, en in CONSERVATION_STATUSES:
        if code not in statuses:
            db.add(ConservationStatus(code=code, color=color))
            db.add_all([ConservationStatusTranslation(status_code=code, lang="vi", name=vi),
                        ConservationStatusTranslation(status_code=code, lang="en", name=en)])

    categories = set(await db.scalars(select(Category.code)))
    for code, vi, en in CATEGORIES:
        if code not in categories:
            category = Category(code=code)
            db.add(category)
            await db.flush()  # await: chờ CSDL cấp category.id cho bản dịch
            db.add_all([CategoryTranslation(category_id=category.id, lang="vi", name=vi),
                        CategoryTranslation(category_id=category.id, lang="en", name=en)])

    if await db.get(SystemSettings, 1) is None:
        db.add(SystemSettings(id=1, zoo_name="ZooGuide", open_hours="07h00-17h00",
                              auto_approve=False, default_lang="vi"))

    # ponytail: 1 khu mẫu để thêm được động vật khi CSDL chưa có khu nào (không có API thêm khu vực)
    if await db.scalar(select(Zone.id).limit(1)) is None:
        zone = Zone(color="#4CAF50", open_hours="07h00-17h00")
        db.add(zone)
        await db.flush()
        db.add(ZoneTranslation(zone_id=zone.id, lang="vi", name="Khu mẫu"))
    await db.flush()

    if config.ADMIN_EMAIL and config.ADMIN_PASSWORD:
        email = config.ADMIN_EMAIL.lower()
        if await db.scalar(select(User).where(User.email == email)) is None:
            admin_role = await db.scalar(select(Role).where(Role.code == "admin"))
            # run_in_threadpool: băm mật khẩu nặng CPU, không chạy thẳng trong event loop
            password_hash = await run_in_threadpool(hash_password, config.ADMIN_PASSWORD)
            db.add(User(full_name="Admin", email=email, role_id=admin_role.id, password_hash=password_hash))
    await db.commit()  # await: chờ SQLite ghi hẳn toàn bộ dữ liệu mặc định
