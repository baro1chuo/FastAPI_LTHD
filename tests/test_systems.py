"""Test nhóm SYSTEMS (UC15 Thống kê, UC16 Cài đặt) và các API chỉ đọc (khu vực, nhóm, health)."""


def test_dashboard_counts(client, admin, user):
    """UC15: thống kê đúng số liệu dữ liệu mẫu; chỉ admin xem được (user -> 403)."""
    data = client.get("/api/systems/dashboard", headers=admin).json()
    assert data["total_animals"] == 18 and data["total_users"] == 5
    assert data["reviews_by_status"] == {"pending": 3, "approved": 8, "hidden": 1}
    assert client.get("/api/systems/dashboard", headers=user).status_code == 403


def test_settings_validation(client, admin):
    """UC16 E1: giờ mở cửa sau giờ đóng cửa / sai định dạng -> 422; ngôn ngữ không hỗ trợ -> 400."""
    assert client.put("/api/systems/settings", json={"open_hours": "17h00-07h00"}, headers=admin).status_code == 422
    assert client.put("/api/systems/settings", json={"hotline": "abc"}, headers=admin).status_code == 422
    assert client.put("/api/systems/settings", json={"default_lang": "fr"}, headers=admin).status_code == 400
    res = client.put("/api/systems/settings", json={"open_hours": "08h00-18h00"}, headers=admin)
    assert res.status_code == 200 and res.json()["open_hours"] == "08h00-18h00"


def test_enable_auto_approve_keeps_pending_reviews(client, admin):
    """UC16: bật tự duyệt KHÔNG đổi các đánh giá đang chờ duyệt."""
    client.put("/api/systems/settings", json={"auto_approve": True}, headers=admin)
    assert client.get("/api/systems/dashboard", headers=admin).json()["reviews_by_status"]["pending"] == 3


def test_zones_and_categories_by_language(client):
    """UC01: danh sách khu vực và nhóm động vật đổi theo ngôn ngữ (dùng làm bộ lọc)."""
    assert client.get("/api/categories", params={"lang": "en"}).json()[0]["name"] == "Mammals"
    assert "Carnivore Zone" in [z["name"] for z in client.get("/api/zones", params={"lang": "en"}).json()]


def test_health(client):
    """/api/health trả {"status": "ok"}."""
    assert client.get("/api/health").json() == {"status": "ok"}
