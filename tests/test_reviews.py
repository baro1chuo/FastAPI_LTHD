"""Test nhóm ĐÁNH GIÁ: UC04 Xem, UC09 Gửi, UC10 Của tôi, UC12 Sửa/xóa của tôi, UC13 Duyệt/ẩn/xóa (admin)."""


def _enable_auto_approve(client, admin, value: bool):
    """Bật/tắt cài đặt tự duyệt đánh giá qua API systems (UC16)."""
    assert client.put("/api/systems/settings", json={"auto_approve": value}, headers=admin).status_code == 200


def test_public_reviews_only_approved_with_names(client, animal_ids):
    """UC04: khách chỉ thấy đánh giá đã duyệt, có tên người viết, tổng số và điểm trung bình."""
    page = client.get("/api/reviews", params={"animal_id": animal_ids["Panthera tigris"]}).json()
    assert page["total"] == 3 and page["average"] == 4.7
    assert all(item["status"] == "approved" and item["user_name"] for item in page["items"])


def test_create_review_pending_then_duplicate_409(client, user, animal_ids):
    """UC09: đánh giá mới ở trạng thái pending khi tắt tự duyệt; đánh giá lần 2 cùng động vật -> 409 (E2)."""
    bear = animal_ids["Ursus thibetanus"]
    res = client.post("/api/reviews", json={"animal_id": bear, "rating": 4, "comment": "Hay"}, headers=user)
    assert res.status_code == 201 and res.json()["status"] == "pending"
    assert client.post("/api/reviews", json={"animal_id": bear, "rating": 5}, headers=user).status_code == 409


def test_create_review_auto_approve(client, admin, user, animal_ids):
    """UC09 + UC16: bật tự duyệt thì đánh giá mới được duyệt ngay (không xét số sao)."""
    _enable_auto_approve(client, admin, True)
    res = client.post("/api/reviews", json={"animal_id": animal_ids["Ursus thibetanus"], "rating": 1}, headers=user)
    assert res.json()["status"] == "approved"


def test_review_hidden_animal_404_and_invalid_rating_422(client, user, animal_ids):
    """UC09 E3: đánh giá động vật đang ẩn -> 404; E1: số sao ngoài 1–5 -> 422."""
    hidden = animal_ids["Ambystoma mexicanum"]
    assert client.post("/api/reviews", json={"animal_id": hidden, "rating": 5}, headers=user).status_code == 404
    bear = animal_ids["Ursus thibetanus"]
    assert client.post("/api/reviews", json={"animal_id": bear, "rating": 6}, headers=user).status_code == 422


def test_my_reviews_include_all_statuses(client, user):
    """UC10: người dùng thấy MỌI đánh giá của mình (kể cả pending), kèm tên động vật."""
    mine = client.get("/api/reviews/me", headers=user).json()
    assert {r["status"] for r in mine} >= {"approved", "pending"}
    assert all(r["animal_name"] for r in mine)


def test_update_own_review_resets_to_pending(client, admin, user, animal_ids):
    """UC12: sửa đánh giá của mình -> nội dung mới, trạng thái về pending để duyệt lại."""
    tiger = animal_ids["Panthera tigris"]
    review = next(r for r in client.get("/api/reviews/me", headers=user).json() if r["animal_id"] == tiger)
    assert review["status"] == "approved"
    res = client.patch(f"/api/reviews/me/{review['id']}", json={"comment": "Sửa lại"}, headers=user)
    assert res.status_code == 200 and res.json()["comment"] == "Sửa lại" and res.json()["status"] == "pending"


def test_cannot_edit_or_delete_others_review(client, user, other_user):
    """UC12 E2: không sửa/xóa được đánh giá của người khác (403)."""
    review_id = client.get("/api/reviews/me", headers=user).json()[0]["id"]
    assert client.patch(f"/api/reviews/me/{review_id}", json={"rating": 1}, headers=other_user).status_code == 403
    assert client.delete(f"/api/reviews/me/{review_id}", headers=other_user).status_code == 403


def test_delete_own_review_then_can_review_again(client, user):
    """UC12 A1: xóa đánh giá của mình rồi được gửi đánh giá mới cho động vật đó."""
    review = client.get("/api/reviews/me", headers=user).json()[0]
    assert client.delete(f"/api/reviews/me/{review['id']}", headers=user).status_code == 204
    again = client.post("/api/reviews", json={"animal_id": review["animal_id"], "rating": 5}, headers=user)
    assert again.status_code == 201


def test_admin_moderation_and_search(client, admin, user):
    """UC13: admin lọc theo trạng thái, tìm theo tên người viết, ẩn đánh giá; user thường -> 403."""
    pending = client.get("/api/reviews/all", params={"status": "pending"}, headers=admin).json()
    assert pending["total"] == 3
    found = client.get("/api/reviews/search", params={"username": "bình"}, headers=admin).json()
    assert found["total"] == 3 and {r["user_name"] for r in found["items"]} == {"Trần Thị Bình"}
    review_id = pending["items"][0]["id"]
    assert client.patch(f"/api/reviews/{review_id}", json={"status": "hidden"}, headers=admin).json()["status"] == "hidden"
    assert client.get("/api/reviews/all", headers=user).status_code == 403
    assert client.delete(f"/api/reviews/{review_id}", headers=admin).status_code == 204
