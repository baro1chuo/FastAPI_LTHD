"""Cấu hình chung cho pytest: mỗi test chạy trên một CSDL SQLite RIÊNG (file tạm), tạo bằng chính migration
Alembic như khi triển khai thật, rồi nạp dữ liệu mẫu (app/core/sample_data.py).

Chạy: python -m pytest -v
"""
import os
import tempfile
from pathlib import Path

# Đặt DATABASE_URL TRƯỚC khi import app: app/core/config.py đọc biến môi trường lúc được import
_TMP_DIR = Path(tempfile.mkdtemp(prefix="zooguide_test_"))
os.environ["DATABASE_URL"] = f"sqlite+aiosqlite:///{(_TMP_DIR / 'test.db').as_posix()}"

import pytest  # noqa: E402
from alembic import command  # noqa: E402
from alembic.config import Config  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from app.core import config  # noqa: E402
from app.core.database import SessionLocal  # noqa: E402
from app.core.sample_data import load_sample_data  # noqa: E402
from app.main import app  # noqa: E402

ROOT = Path(__file__).resolve().parent.parent
PASSWORD = "12345678"  # mật khẩu chung của tài khoản mẫu


@pytest.fixture
def client(tmp_path, monkeypatch):
    """TestClient trên CSDL sạch: xóa hết bảng, chạy lại migration, seed + dữ liệu mẫu. Ảnh tải lên ghi vào thư mục tạm."""
    alembic_cfg = Config(str(ROOT / "alembic.ini"))
    command.downgrade(alembic_cfg, "base")  # xóa mọi bảng của test trước
    command.upgrade(alembic_cfg, "head")    # tạo lại bảng đúng như migration
    monkeypatch.setattr(config, "UPLOAD_DIR", tmp_path / "uploads")  # không ghi ảnh test vào thư mục dự án

    async def _load():
        async with SessionLocal() as db:
            await load_sample_data(db)

    with TestClient(app) as c:  # "with" để chạy lifespan -> init_db() -> seed dữ liệu mặc định
        # Chạy hàm async trong CÙNG event loop với app (c.portal): kết nối aiosqlite gắn với 1 event loop
        c.portal.call(_load)
        yield c
        # lifespan tự engine.dispose() khi thoát "with": test sau mở kết nối mới trên event loop mới


def login(client: TestClient, email: str, password: str = PASSWORD) -> dict:
    """Đăng nhập rồi trả header Authorization dùng cho các request cần token."""
    res = client.post("/api/auth/login", json={"email": email, "password": password})
    assert res.status_code == 200, res.text
    return {"Authorization": f"Bearer {res.json()['token']}"}


@pytest.fixture
def admin(client):
    """Header của tài khoản admin mẫu (admin@zooguide.vn)."""
    return login(client, "admin@zooguide.vn")


@pytest.fixture
def user(client):
    """Header của user mẫu Nguyễn Văn An (an@zooguide.vn)."""
    return login(client, "an@zooguide.vn")


@pytest.fixture
def other_user(client):
    """Header của user mẫu thứ hai Trần Thị Bình (binh@zooguide.vn)."""
    return login(client, "binh@zooguide.vn")


@pytest.fixture
def animal_ids(client, admin):
    """Bảng tra id động vật theo tên khoa học (admin xem được cả động vật đang ẩn)."""
    items = client.get("/api/animals", params={"size": 100}, headers=admin).json()["items"]
    return {item["scientific_name"]: item["id"] for item in items}
