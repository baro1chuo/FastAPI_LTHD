"""Kiểm tra API trên server ĐANG CHẠY (HTTPS): gọi lần lượt đủ 33 endpoint, in kết quả từng request.

Cách chạy (server phải đang chạy và đã nạp dữ liệu mẫu bằng python -m app.core.sample_data):
    python kiem_tra_api.py                              # mặc định https://127.0.0.1:8000
    python kiem_tra_api.py https://127.0.0.1:8001      # nếu server chạy cổng khác

Dữ liệu tạo ra để thử (tài khoản, động vật, đánh giá) được xóa ở cuối; các cài đặt bị đổi được trả về như cũ.
Chỉ còn sót lại file ảnh thử trong app/static/uploads/.
"""
import sys
import uuid
from pathlib import Path

import httpx

BASE_URL = sys.argv[1] if len(sys.argv) > 1 else "https://127.0.0.1:8000"
CERT = Path(__file__).parent / "certs" / "cert.pem"  # chứng chỉ tự ký: dùng để xác thực HTTPS
ADMIN = {"email": "admin@zooguide.vn", "password": "12345678"}
PNG = b"\x89PNG\r\n\x1a\n" + b"\x00" * 64  # ảnh PNG giả (đúng chữ ký file)

results = {"ok": 0, "fail": 0}


def check(name: str, res: httpx.Response, expected: int) -> httpx.Response:
    """In 1 dòng kết quả: đúng mã HTTP mong đợi thì ✓, sai thì ✗ kèm nội dung lỗi."""
    passed = res.status_code == expected
    results["ok" if passed else "fail"] += 1
    mark = "✓" if passed else "✗"
    line = f"  {mark} {res.request.method:6} {res.request.url.path:38} {res.status_code} (cần {expected})  {name}"
    if not passed:
        line += f"\n      -> {res.text[:200]}"
    print(line)
    return res


def bearer(token: str) -> dict:
    """Header Authorization cho request cần đăng nhập."""
    return {"Authorization": f"Bearer {token}"}


def main() -> None:
    """Chạy toàn bộ kịch bản kiểm tra theo nhóm API."""
    with httpx.Client(base_url=BASE_URL, verify=str(CERT) if CERT.exists() else False, timeout=30) as c:
        print(f"Server: {BASE_URL}\n")

        print("[Health]")
        check("server còn sống", c.get("/api/health"), 200)

        print("\n[Auth]")
        email = f"test_{uuid.uuid4().hex[:8]}@zooguide.vn"  # email ngẫu nhiên để chạy lại nhiều lần không trùng
        user_body = {"full_name": "Người Thử", "email": email, "password": "matkhau123"}
        check("đăng ký", c.post("/api/auth/register", json=user_body), 201)
        check("đăng ký trùng email -> 409", c.post("/api/auth/register", json=user_body), 409)
        check("mật khẩu ngắn -> 422", c.post("/api/auth/register", json={**user_body, "password": "123"}), 422)
        check("sai mật khẩu -> 401", c.post("/api/auth/login", json={"email": email, "password": "sai12345"}), 401)
        u_token = check("đăng nhập user", c.post("/api/auth/login", json={"email": email, "password": "matkhau123"}),
                        200).json()["token"]
        res = check("đăng nhập admin", c.post("/api/auth/login", json=ADMIN), 200)
        if res.status_code != 200:
            print("\nKhông đăng nhập được admin -> hãy chạy: python -m app.core.sample_data")
            return
        a_token = res.json()["token"]
        U, A = bearer(u_token), bearer(a_token)
        check("user hiện tại", c.get("/api/auth/me", headers=U), 200)
        check("không token -> 401", c.get("/api/auth/me"), 401)
        check("đăng xuất", c.post("/api/auth/logout", headers=U), 204)

        print("\n[Users]")
        me = check("xem hồ sơ", c.get("/api/users/me", headers=U), 200).json()
        check("sửa họ tên", c.patch("/api/users/me", json={"full_name": "Người Thử 2"}, headers=U), 200)
        pw = {"current_password": "sai00000", "new_password": "matkhau456", "confirm_password": "matkhau456"}
        check("đổi mật khẩu, sai mật khẩu cũ -> 400", c.patch("/api/users/me", json={"password": pw}, headers=U), 400)
        check("upload avatar", c.post(f"/api/users/{me['id']}/image",
                                      files={"file": ("a.png", PNG, "image/png")}, headers=U), 200)
        admin_id = c.get("/api/users/me", headers=A).json()["id"]
        check("upload avatar người khác -> 403", c.post(f"/api/users/{admin_id}/image",
                                                       files={"file": ("a.png", PNG, "image/png")}, headers=U), 403)
        check("danh sách tài khoản (admin)", c.get("/api/users", params={"search": "test_"}, headers=A), 200)
        check("danh sách tài khoản (user) -> 403", c.get("/api/users", headers=U), 403)
        check("chi tiết tài khoản", c.get(f"/api/users/{me['id']}", headers=A), 200)
        check("khóa tài khoản", c.patch(f"/api/users/{me['id']}/status", json={"status": "locked"}, headers=A), 200)
        check("tài khoản bị khóa -> 403", c.get("/api/users/me", headers=U), 403)
        check("mở khóa", c.patch(f"/api/users/{me['id']}/status", json={"status": "active"}, headers=A), 200)
        check("admin tự khóa mình -> 403",
              c.patch(f"/api/users/{admin_id}/status", json={"status": "locked"}, headers=A), 403)

        print("\n[Zones / Categories]")
        zone_id = check("danh sách khu vực", c.get("/api/zones", params={"lang": "en"}), 200).json()[0]["id"]
        category_id = check("danh sách nhóm động vật", c.get("/api/categories"), 200).json()[0]["id"]

        print("\n[Animals]")
        check("danh sách (khách)", c.get("/api/animals", params={"q": "Hổ"}), 200)
        check("danh sách (admin, gồm động vật ẩn)", c.get("/api/animals", headers=A), 200)
        animal_body = {
            "scientific_name": f"Testus {uuid.uuid4().hex[:8]}", "zone_id": zone_id, "category_id": category_id,
            "conservation_status_code": "LC",
            "translations": [{"lang": "vi", "name": f"Thú thử {uuid.uuid4().hex[:6]}"}],
        }
        check("thêm động vật (user) -> 403", c.post("/api/animals", json=animal_body, headers=U), 403)
        animal_id = check("thêm động vật", c.post("/api/animals", json=animal_body, headers=A), 201).json()["id"]
        check("thêm trùng tên khoa học -> 409", c.post("/api/animals", json=animal_body, headers=A), 409)
        check("chi tiết", c.get(f"/api/animals/{animal_id}", params={"lang": "vi"}), 200)
        check("động vật liên quan", c.get(f"/api/animals/{animal_id}/related", params={"limit": 3}), 200)
        check("ẩn động vật (xóa mềm)", c.patch(f"/api/animals/{animal_id}", json={"available": False}, headers=A), 200)
        check("khách xem động vật ẩn -> 404", c.get(f"/api/animals/{animal_id}"), 404)
        check("hiện lại", c.patch(f"/api/animals/{animal_id}", json={"available": True}, headers=A), 200)
        check("upload ảnh động vật", c.post(f"/api/animals/{animal_id}/image",
                                            files={"file": ("x.png", PNG, "image/png")}, headers=A), 200)

        print("\n[Reviews]")
        review = check("gửi đánh giá", c.post("/api/reviews", json={"animal_id": animal_id, "rating": 5,
                                                                     "comment": "Thử"}, headers=U), 201).json()
        check("đánh giá lần 2 -> 409", c.post("/api/reviews", json={"animal_id": animal_id, "rating": 4}, headers=U), 409)
        check("số sao 6 -> 422", c.post("/api/reviews", json={"animal_id": animal_id, "rating": 6}, headers=U), 422)
        check("đánh giá công khai", c.get("/api/reviews", params={"animal_id": animal_id}), 200)
        check("đánh giá của tôi", c.get("/api/reviews/me", headers=U), 200)
        check("sửa đánh giá của tôi", c.patch(f"/api/reviews/me/{review['id']}", json={"comment": "Sửa"}, headers=U), 200)
        check("admin sửa qua /me (không phải của mình) -> 403",
              c.patch(f"/api/reviews/me/{review['id']}", json={"rating": 1}, headers=A), 403)
        check("mọi đánh giá (admin)", c.get("/api/reviews/all", params={"status": "pending"}, headers=A), 200)
        check("tìm theo tên người viết", c.get("/api/reviews/search", params={"username": "Người Thử"}, headers=A), 200)
        check("duyệt đánh giá", c.patch(f"/api/reviews/{review['id']}", json={"status": "approved"}, headers=A), 200)
        check("xóa đánh giá của tôi", c.delete(f"/api/reviews/me/{review['id']}", headers=U), 204)
        review2 = c.post("/api/reviews", json={"animal_id": animal_id, "rating": 3}, headers=U).json()
        check("admin xóa đánh giá", c.delete(f"/api/reviews/{review2['id']}", headers=A), 204)

        print("\n[Systems]")
        check("thống kê", c.get("/api/systems/dashboard", headers=A), 200)
        check("thống kê (user) -> 403", c.get("/api/systems/dashboard", headers=U), 403)
        old = check("xem cài đặt", c.get("/api/systems/settings", headers=A), 200).json()
        check("giờ mở sau giờ đóng -> 422",
              c.put("/api/systems/settings", json={"open_hours": "17h00-07h00"}, headers=A), 422)
        check("đổi hotline", c.put("/api/systems/settings", json={"hotline": "1900 1234"}, headers=A), 200)
        c.put("/api/systems/settings", json={"hotline": old["hotline"]}, headers=A)  # trả lại như cũ

        print("\n[Dọn dữ liệu thử]")
        check("xóa động vật thử", c.delete(f"/api/animals/{animal_id}", headers=A), 204)
        check("xóa tài khoản thử", c.delete(f"/api/users/{me['id']}", headers=A), 204)

    total = results["ok"] + results["fail"]
    print(f"\nKết quả: {results['ok']}/{total} đúng" + ("" if not results["fail"] else f", {results['fail']} SAI"))
    sys.exit(1 if results["fail"] else 0)


if __name__ == "__main__":
    try:
        main()
    except httpx.ConnectError:
        print(f"Không kết nối được {BASE_URL}. Server đã chạy chưa? (python -m uvicorn app.main:app "
              "--ssl-keyfile certs/key.pem --ssl-certfile certs/cert.pem)")
        sys.exit(1)
