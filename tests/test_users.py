"""Test nhóm NGƯỜI DÙNG: UC08 Hồ sơ, UC14 Quản lý tài khoản."""
from tests.conftest import login

PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64  # 8 byte chữ ký PNG + dữ liệu giả


def test_update_profile_cannot_change_email(client, user):
    """UC08: sửa được họ tên; email gửi lên bị bỏ qua (email không được sửa)."""
    res = client.patch("/api/users/me", json={"full_name": "An Nguyễn", "email": "hack@x.com"}, headers=user)
    assert res.status_code == 200
    assert res.json()["full_name"] == "An Nguyễn"
    assert res.json()["email"] == "an@zooguide.vn"


def test_change_password_requires_current_password(client, user):
    """UC08 A1/E2: sai mật khẩu hiện tại -> 400; đúng thì đổi được và đăng nhập bằng mật khẩu mới."""
    body = {"password": {"current_password": "sai00000", "new_password": "moi123456", "confirm_password": "moi123456"}}
    assert client.patch("/api/users/me", json=body, headers=user).status_code == 400
    body["password"]["current_password"] = "12345678"
    assert client.patch("/api/users/me", json=body, headers=user).status_code == 200
    login(client, "an@zooguide.vn", "moi123456")


def test_upload_avatar_only_for_self(client, user, admin):
    """UC08: tải ảnh đại diện của chính mình được; đổi ảnh người khác -> 403; file không phải ảnh -> 400."""
    my_id = client.get("/api/users/me", headers=user).json()["id"]
    admin_id = client.get("/api/users/me", headers=admin).json()["id"]
    res = client.post(f"/api/users/{my_id}/image", files={"file": ("a.png", PNG, "image/png")}, headers=user)
    assert res.status_code == 200 and res.json()["avatar"].startswith("/static/uploads/avatars/")
    assert client.post(f"/api/users/{admin_id}/image", files={"file": ("a.png", PNG, "image/png")},
                       headers=user).status_code == 403
    assert client.post(f"/api/users/{my_id}/image", files={"file": ("a.png", b"khong phai anh", "image/png")},
                       headers=user).status_code == 400


def test_admin_apis_forbidden_for_normal_user(client, user):
    """UC14: user thường gọi API quản lý tài khoản -> 403."""
    assert client.get("/api/users", headers=user).status_code == 403


def test_admin_cannot_lock_or_delete_self(client, admin):
    """UC14 E1: admin không tự khóa / tự xóa chính mình (403)."""
    admin_id = client.get("/api/users/me", headers=admin).json()["id"]
    assert client.patch(f"/api/users/{admin_id}/status", json={"status": "locked"}, headers=admin).status_code == 403
    assert client.delete(f"/api/users/{admin_id}", headers=admin).status_code == 403


def test_status_update_has_no_role_change(client, admin, user):
    """UC14: chỉ khóa/mở khóa; gửi role_id (đổi vai trò) không hợp lệ -> 422."""
    user_id = client.get("/api/users/me", headers=user).json()["id"]
    assert client.patch(f"/api/users/{user_id}/status", json={"role_id": 1}, headers=admin).status_code == 422


def test_delete_user_also_deletes_reviews(client, admin, user):
    """UC14 A2: xóa tài khoản thì đánh giá của tài khoản đó bị xóa theo (ON DELETE CASCADE)."""
    user_id = client.get("/api/users/me", headers=user).json()["id"]
    before = client.get("/api/reviews/all", params={"size": 100}, headers=admin).json()["total"]
    mine = len(client.get("/api/reviews/me", headers=user).json())
    assert client.delete(f"/api/users/{user_id}", headers=admin).status_code == 204
    after = client.get("/api/reviews/all", params={"size": 100}, headers=admin).json()["total"]
    assert mine > 0 and after == before - mine
