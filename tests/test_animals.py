"""Test nhóm ĐỘNG VẬT: UC01 Xem/tìm/lọc, UC02 Chi tiết, UC03 Liên quan, UC11 Quản lý động vật (ẩn/hiện = xóa mềm)."""

JPG = b"\xff\xd8\xff\xe0" + b"\x00" * 64  # chữ ký JPEG + dữ liệu giả
NEW_ANIMAL = {
    "scientific_name": "Felis catus", "zone_id": 1, "category_id": 1, "conservation_status_code": "LC",
    "translations": [{"lang": "vi", "name": "Mèo nhà"}, {"lang": "en", "name": "Cat"}],
}


def test_guest_sees_only_available_animals(client, admin):
    """UC01 + quy tắc available: khách chỉ thấy động vật đang hiển thị; admin (gửi token) thấy cả động vật ẩn."""
    guest = client.get("/api/animals", params={"size": 100}).json()
    staff = client.get("/api/animals", params={"size": 100}, headers=admin).json()
    assert all(item["available"] for item in guest["items"])
    assert staff["total"] == guest["total"] + 1  # dữ liệu mẫu có đúng 1 động vật ẩn (Kỳ giông Mexico)


def test_search_and_filter(client):
    """UC01: tìm gần đúng theo tên hiển thị ("Hổ" ra cả Hổ và Rắn hổ mang chúa) / tên khoa học; lọc theo nhóm."""
    by_name = {a["scientific_name"] for a in client.get("/api/animals", params={"q": "Hổ"}).json()["items"]}
    assert by_name == {"Panthera tigris", "Ophiophagus hannah"}
    by_sci = client.get("/api/animals", params={"q": "tigris"}).json()["items"]
    assert [a["scientific_name"] for a in by_sci] == ["Panthera tigris"]
    birds = client.get("/api/animals", params={"category_id": 2}).json()["items"]
    assert birds and all(a["category_id"] == 2 for a in birds)


def test_detail_language_and_hidden_404(client, admin, animal_ids):
    """UC02: chi tiết theo ngôn ngữ; động vật đang ẩn -> 404 với khách (E1), admin vẫn xem được."""
    tiger = animal_ids["Panthera tigris"]
    assert client.get(f"/api/animals/{tiger}", params={"lang": "en"}).json()["name"] == "Tiger"
    hidden = animal_ids["Ambystoma mexicanum"]
    assert client.get(f"/api/animals/{hidden}").status_code == 404
    assert client.get(f"/api/animals/{hidden}", headers=admin).status_code == 200


def test_related_excludes_self_and_hidden(client, animal_ids):
    """UC03: động vật liên quan không gồm chính nó và không gồm động vật đang ẩn."""
    croc = animal_ids["Crocodylus siamensis"]
    related = [a["id"] for a in client.get(f"/api/animals/{croc}/related", params={"limit": 20}).json()]
    assert related and croc not in related and animal_ids["Ambystoma mexicanum"] not in related


def test_create_animal_admin_only_and_duplicate_409(client, admin, user):
    """UC11: chỉ admin thêm được (user -> 403); mặc định available=true; trùng tên khoa học -> 409 (E2)."""
    assert client.post("/api/animals", json=NEW_ANIMAL, headers=user).status_code == 403
    res = client.post("/api/animals", json=NEW_ANIMAL, headers=admin)
    assert res.status_code == 201 and res.json()["available"] is True
    assert client.post("/api/animals", json=NEW_ANIMAL, headers=admin).status_code == 409


def test_patch_hide_and_show_soft_delete(client, admin, animal_ids):
    """UC11 A2 (xóa mềm): PATCH {"available": false} ẩn động vật khỏi khách; true thì hiện lại; field khác giữ nguyên."""
    tiger = animal_ids["Panthera tigris"]
    res = client.patch(f"/api/animals/{tiger}", json={"available": False}, headers=admin)
    assert res.status_code == 200 and res.json()["scientific_name"] == "Panthera tigris"
    assert client.get(f"/api/animals/{tiger}").status_code == 404
    client.patch(f"/api/animals/{tiger}", json={"available": True}, headers=admin)
    assert client.get(f"/api/animals/{tiger}").status_code == 200


def test_patch_only_changes_sent_fields(client, admin, animal_ids):
    """UC11 A1: PATCH chỉ đổi field được gửi (exclude_unset); gửi null cho cột bắt buộc -> 422."""
    tiger = animal_ids["Panthera tigris"]
    before = client.get(f"/api/animals/{tiger}", headers=admin).json()
    after = client.patch(f"/api/animals/{tiger}", json={"popularity": 1}, headers=admin).json()
    assert after["popularity"] == 1 and after["zone_id"] == before["zone_id"]
    assert client.patch(f"/api/animals/{tiger}", json={"zone_id": None}, headers=admin).status_code == 422


def test_delete_animal_cascades_reviews(client, admin, animal_ids):
    """UC11 A3: xóa động vật thì xóa luôn đánh giá của nó (ON DELETE CASCADE)."""
    tiger = animal_ids["Panthera tigris"]
    assert client.get("/api/reviews/all", params={"animal_id": tiger}, headers=admin).json()["total"] > 0
    assert client.delete(f"/api/animals/{tiger}", headers=admin).status_code == 204
    assert client.get("/api/reviews/all", params={"animal_id": tiger}, headers=admin).json()["total"] == 0


def test_upload_animal_image(client, admin, user, animal_ids):
    """UC11: admin tải ảnh động vật (multipart); user thường -> 403; content_type không phải ảnh -> 400."""
    tiger = animal_ids["Panthera tigris"]
    res = client.post(f"/api/animals/{tiger}/image", files={"file": ("t.jpg", JPG, "image/jpeg")}, headers=admin)
    assert res.status_code == 200 and res.json()["image"].endswith(".jpg")
    assert client.post(f"/api/animals/{tiger}/image", files={"file": ("t.jpg", JPG, "image/jpeg")},
                       headers=user).status_code == 403
    assert client.post(f"/api/animals/{tiger}/image", files={"file": ("t.txt", b"abc", "text/plain")},
                       headers=admin).status_code == 400
