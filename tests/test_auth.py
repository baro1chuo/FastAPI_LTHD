"""Test nhóm XÁC THỰC: UC06 Đăng ký, UC07 Đăng nhập, UC05 Đăng xuất, quy tắc JWT."""
from app.core.database import SessionLocal
from app.repositories import user_repository
from tests.conftest import login


def test_register_success_stores_hash_and_lowercase_email(client):
    """UC06: đăng ký thành công trả 201, email chuẩn hóa chữ thường, CSDL chỉ lưu HASH mật khẩu."""
    res = client.post("/api/auth/register",
                      json={"full_name": "Khách Mới", "email": "Moi@Example.com", "password": "matkhau123"})
    assert res.status_code == 201
    assert res.json()["email"] == "moi@example.com"
    assert "password" not in res.text  # không trả mật khẩu/hash ra ngoài
    with SessionLocal() as db:
        stored = user_repository.get_by_email(db, "moi@example.com").password_hash
    assert stored != "matkhau123" and stored.startswith("pbkdf2_sha256$")


def test_register_duplicate_email_409(client):
    """UC06 E2: email đã đăng ký -> 409."""
    res = client.post("/api/auth/register",
                      json={"full_name": "Trùng", "email": "an@zooguide.vn", "password": "matkhau123"})
    assert res.status_code == 409


def test_register_short_password_422(client):
    """UC06 E1: mật khẩu dưới 8 ký tự -> 422 (Pydantic chặn trước khi vào service)."""
    res = client.post("/api/auth/register", json={"full_name": "A", "email": "a@x.com", "password": "123"})
    assert res.status_code == 422


def test_login_wrong_password_and_unknown_email_same_message(client):
    """UC07 E2: sai mật khẩu và email không tồn tại cùng trả 401 với CÙNG thông báo (không lộ email nào đã đăng ký)."""
    wrong_pw = client.post("/api/auth/login", json={"email": "an@zooguide.vn", "password": "sai12345"})
    unknown = client.post("/api/auth/login", json={"email": "khongco@x.com", "password": "sai12345"})
    assert wrong_pw.status_code == unknown.status_code == 401
    assert wrong_pw.json() == unknown.json()


def test_locked_account_cannot_login_or_use_old_token(client, admin, user):
    """UC07 E3 + UC14: tài khoản bị khóa không đăng nhập được (403), token cũ cũng bị chặn ngay (403)."""
    user_id = client.get("/api/users/me", headers=user).json()["id"]
    assert client.patch(f"/api/users/{user_id}/status", json={"status": "locked"}, headers=admin).status_code == 200
    assert client.post("/api/auth/login", json={"email": "an@zooguide.vn", "password": "12345678"}).status_code == 403
    assert client.get("/api/users/me", headers=user).status_code == 403


def test_protected_api_requires_valid_token(client):
    """Quy tắc JWT: thiếu token hoặc token giả -> 401."""
    assert client.get("/api/auth/me").status_code == 401
    assert client.get("/api/auth/me", headers={"Authorization": "Bearer token-gia"}).status_code == 401


def test_login_returns_token_usable_for_me(client):
    """UC07: đăng nhập trả JWT; gửi kèm header Authorization thì /api/auth/me trả đúng người."""
    headers = login(client, "an@zooguide.vn")
    assert client.get("/api/auth/me", headers=headers).json()["email"] == "an@zooguide.vn"


def test_logout_returns_204_and_requires_token(client, user):
    """UC05: đăng xuất trả 204 (frontend tự xóa token); không gửi token -> 401."""
    assert client.post("/api/auth/logout", headers=user).status_code == 204
    assert client.post("/api/auth/logout").status_code == 401
