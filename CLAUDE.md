# ZooGuide – Backend FastAPI

## Bài toán
Khách sở thú không biết nên xem con gì, ở khu nào; bảng giới thiệu ngắn, một ngôn ngữ, khó cập nhật.
Ban quản lý sửa thông tin và thu ý kiến khách thủ công. ZooGuide cho:
- **Guest**: tra cứu/lọc động vật (tên, nhóm, khu vực), xem chi tiết, động vật liên quan, đánh giá đã duyệt; nội dung đa ngôn ngữ.
- **User** (đã đăng nhập, kế thừa Guest): đăng ký/đăng nhập, sửa hồ sơ, đổi mật khẩu, gửi đánh giá, xem/sửa/xóa đánh giá của mình.
- **Admin** (kế thừa User): quản lý động vật (thêm/sửa/ẩn-hiện/xóa), tài khoản (khóa/mở khóa/xóa); duyệt/ẩn/xóa đánh giá; thống kê; cài đặt hệ thống.
- Khu vực được nạp sẵn (seed), không có chức năng quản lý khu vực. Role `staff` có trong seed nhưng không dùng trong API.
- Ngoài phạm vi hiện tại: bản đồ & tuyến tham quan (bảng MAP_POINT có sẵn nhưng làm sau), QR, chatbot, yêu thích.

## Kiến trúc & thư mục
Router → Dependency (xác thực/phân quyền) → Service → Repository → Model (SQLAlchemy) → CSDL SQLite. Toàn bộ chuỗi có I/O là **async** (aiosqlite).
```
app/
  main.py        tạo app, CORS, handler lỗi nghiệp vụ, include router, mount /static
  core/          config.py, database.py (async engine, get_db, init_db), security.py (PBKDF2, JWT),
                 deps.py (get_current_user, get_optional_user, require_admin, require_token), exceptions.py,
                 seed.py (dữ liệu mặc định lúc khởi động), sample_data.py (dữ liệu mẫu: python -m app.core.sample_data)
  models/        SQLAlchemy 2.0 – bảng theo ERD. Thuộc tính Python snake_case, tên cột DB camelCase (vd zone_id -> "zoneId")
  schemas/       Pydantic v2 – dữ liệu vào/ra API
  routers/       mỗi file = 1 nhóm trong bảng Đặc tả API; router mỏng, chỉ gọi service
  services/      logic nghiệp vụ: animal, review, user, auth, stats, settings, zone, category, image, i18n
  repositories/  câu truy vấn (không commit, không quy tắc nghiệp vụ)
  static/uploads/  ảnh tải lên (không đưa lên git)
alembic/         migration cấu trúc bảng (alembic/versions/*.py)
tests/           pytest: python -m pytest
docs/NHAT_KY_CODE.md  nhật ký từng bước code (đưa vào báo cáo)
```

## Chạy dự án (sau khi git pull)
```
pip install -r requirements.txt
python -m alembic upgrade head          # tạo/cập nhật bảng trong app/database/zoo.db
python -m app.core.sample_data          # (tùy chọn) nạp dữ liệu mẫu; mật khẩu tài khoản mẫu 12345678
python -m uvicorn app.main:app --reload # mở http://127.0.0.1:8000/docs
```
seed.py tự thêm dữ liệu mặc định (ngôn ngữ, vai trò, mức bảo tồn, nhóm, cài đặt) mỗi lần khởi động. `zoo.db` không lên git.

## Quy ước code
- Router không chứa logic nghiệp vụ, không query DB trực tiếp; gọi `services/*`. Service gọi `repositories/*`; repository không commit.
- Service raise exception nghiệp vụ (NotFound 404, Conflict 409, Forbidden 403, Auth 401, BusinessRule 400); main.py đổi sang HTTP `{"detail": ...}`.
- Validation kiểu/định dạng đặt ở Pydantic (lỗi 422); kiểm tra cần tra DB (trùng email, khóa ngoại tồn tại…) đặt ở service.
- Mọi đường dẫn bắt đầu bằng `/api`. Auth bằng JWT: `Authorization: Bearer <token>`. Đăng nhập dùng POST.
- Ngôn ngữ: frontend gửi `lang`; GET dùng query `?lang=vi`, POST/PATCH gửi trong body. Thiếu bản dịch -> dùng `defaultLang` trong SYSTEM_SETTINGS (`services/i18n.py`).
- **Async:** hàm có I/O là `async def` + `await` (db.get/scalar/scalars/execute/flush/merge/delete/commit/refresh). Không gọi hàm chặn trong async def; băm/kiểm tra mật khẩu và ghi file đi qua `run_in_threadpool`. Không `asyncio.gather` trên cùng một AsyncSession. Không lazy load (User.role dùng lazy="joined"; cột server_default đọc sau commit thì `await db.refresh`).
- **Alembic:** mọi thay đổi trong app/models phải kèm một migration mới trong alembic/versions, commit chung. Không dùng `create_all`, không sửa bảng trực tiếp. Đổi tên cột / sửa CHECK tự viết bằng `op.batch_alter_table`. Mọi ràng buộc có tên (ck_ ghi tay; pk_/uq_/fk_ theo NAMING_CONVENTION trong models/base.py). Đọc lại migration, thử `downgrade -1` rồi `upgrade head`.
- SQLite: luôn bật `PRAGMA foreign_keys = ON` mỗi kết nối (core/database.py).
- Không thêm thư viện mới nếu stdlib/thư viện sẵn có làm được. Code tối giản.
- Branch: mỗi thành viên làm trên branch riêng (bao, tong, …), PR vào `main`.

## CSDL (ERD draw.io Trang-1)
LANGUAGE(code PK, name, isActive) · ROLE(id, code∈admin/staff/user, name)
USER(id, fullName, email UK, passwordHash, roleId FK RESTRICT, status∈active/locked, createdAt, avatar)
ZONE(id, color #RRGGBB, openHours "07h00-17h00", areaM2>0, image) · ZONE_TRANSLATION(zoneId+lang PK, name, description; UNIQUE(lang,name))
CATEGORY(id, code UK) · CATEGORY_TRANSLATION(categoryId+lang PK, name)
CONSERVATION_STATUS(code∈EX,EW,CR,EN,VU,NT,LC,DD,NE, color) · CONSERVATION_STATUS_TRANSLATION
ANIMAL(id, scientificName UK, zoneId FK RESTRICT, categoryId FK RESTRICT, conservationStatusCode FK RESTRICT, **available** (1 hiện / 0 ẩn, mặc định 1), popularity>=0, image)
ANIMAL_TRANSLATION(animalId+lang PK, name, appearance, distribution, ecology, behaviour, diet, reproduction, lifespan, ecologicalRole, threat; UNIQUE(lang,name))
REVIEW(id, animalId FK CASCADE, userId FK CASCADE, rating 1–5, comment ≤500, status∈pending/approved/hidden, createdAt, lang; UNIQUE(animalId,userId))
MAP_POINT / MAP_POINT_TRANSLATION (làm sau) · SYSTEM_SETTINGS(id=1, zooName, openHours, hotline, autoApprove, defaultLang)

## Quy tắc nghiệp vụ
- Mỗi user chỉ đánh giá 1 lần / động vật. Đánh giá mới hoặc vừa sửa: `approved` nếu autoApprove bật, ngược lại `pending`. Bật autoApprove không đổi các đánh giá đang pending.
- Khách chỉ thấy đánh giá `approved`; chủ đánh giá thấy mọi trạng thái của mình và chỉ sửa/xóa được đánh giá của mình (403).
- Mật khẩu ≥ 8 ký tự (chỉ lưu hash); email duy nhất, **không sửa được**; tài khoản `locked` không đăng nhập được (403), token cũ cũng bị chặn.
- Admin không được tự khóa/tự xóa chính mình. Không có chức năng đổi vai trò.
- Xóa mềm động vật = `available=false` (PATCH); khách không thấy (404), admin vẫn thấy. Xóa thật (DELETE) xóa luôn đánh giá & bản dịch (TODO: nhóm chốt giữ hay rút về khung).

## Use case (bản chốt UC01–UC16)
UC01 Xem/tìm/lọc động vật · UC02 Chi tiết · UC03 Động vật liên quan (extend UC02) · UC04 Xem đánh giá (extend UC02)
UC05 Đăng xuất (frontend xóa token) · UC06 Đăng ký · UC07 Đăng nhập · UC08 Xem/cập nhật hồ sơ · UC09 Gửi đánh giá
UC10 Đánh giá của tôi · UC11 QL động vật · UC12 Sửa/xóa đánh giá của tôi (extend UC10) · UC13 Duyệt/ẩn/xóa đánh giá
UC14 QL tài khoản · UC15 Thống kê · UC16 Cài đặt hệ thống

## Đặc tả API (bản chốt)
| Method | Path | Quyền | Chức năng |
|---|---|---|---|
| GET | /api/health | Công khai | Kiểm tra backend |
| POST | /api/auth/register | Guest | Đăng ký (UC06) |
| POST | /api/auth/login | Công khai | Đăng nhập, trả JWT (UC07) |
| POST | /api/auth/logout | User, Admin | Trả 204, không đụng CSDL (UC05) |
| GET | /api/auth/me | User | User hiện tại |
| GET / PATCH | /api/users/me | User | Xem / sửa hồ sơ (họ tên, avatar, đổi mật khẩu; không sửa email) (UC08) |
| POST | /api/users/{user_id}/image | User (chính mình) | Upload avatar multipart (UC08) |
| GET | /api/users | Admin | Danh sách, tìm kiếm, lọc trạng thái, phân trang (UC14) |
| GET / DELETE | /api/users/{id} | Admin | Chi tiết / xóa tài khoản (UC14) |
| PATCH | /api/users/{id}/status | Admin | Khóa / mở khóa (UC14) |
| GET | /api/animals | Công khai (admin thấy cả ẩn) | Tìm `q`, lọc category_id, zone_id, sort, phân trang (UC01) |
| GET | /api/animals/{id} | Công khai | Chi tiết theo ngôn ngữ; ẩn -> 404 (UC02) |
| GET | /api/animals/{id}/related | Công khai | Liên quan, chỉ động vật đang hiện, `limit` (UC03) |
| POST / PATCH / DELETE | /api/animals[/{id}] | Admin | Thêm / sửa một phần (gồm ẩn-hiện `available`) / xóa (UC11) |
| POST | /api/animals/{id}/image | Admin | Upload ảnh multipart (UC11) |
| GET | /api/reviews?animal_id= | Công khai | Đánh giá đã duyệt + tên người viết, tổng, điểm TB (UC04) |
| POST | /api/reviews | User | Gửi đánh giá (UC09) |
| GET | /api/reviews/me | User | Đánh giá của tôi, kèm tên động vật (UC10) |
| PATCH / DELETE | /api/reviews/me/{id} | User | Sửa / xóa đánh giá của mình (UC12) |
| GET | /api/reviews/all | Admin | Mọi đánh giá, lọc status/animal_id (UC13) |
| GET | /api/reviews/search?username= | Admin | Tìm theo tên người viết (UC13) |
| PATCH / DELETE | /api/reviews/{id} | Admin | Duyệt-ẩn / xóa (UC13) |
| GET | /api/zones | Công khai | Danh sách khu vực theo ngôn ngữ (UC01) |
| GET | /api/categories | Công khai | Danh sách nhóm động vật theo ngôn ngữ (UC01) |
| GET | /api/systems/dashboard | Admin | Thống kê (UC15) |
| GET / PUT | /api/systems/settings | Admin | Đọc / cập nhật cài đặt (UC16) |


## Tài liệu nhóm
- Báo cáo (Google Doc "LTHD NHÓM 9"): https://docs.google.com/document/d/1D2VkbSZJ0xYTjXR2LUkZ8l2m3XdChxIHU7TzBBVB_l0/edit
  (tab: UC bản chốt + Activity (swimlane), Đặc tả API, Database, Tầng Service, Tầng Repository, Hướng dẫn async (code), Sơ đồ tổ chức thư mục)
- ERD draw.io: https://drive.google.com/file/d/1gQ2U_159n-Bvh6iDDu_rNBc_nQSOCbWR/view
- Phân công: https://docs.google.com/spreadsheets/d/1ir71b6yCG4L3-9vFsDNO07OXZhSECIr20L8xxuKaz3o/edit
  (Hùng: tầng CSDL · Bảo: router · Tòng: service, activity diagram · Bảo+Tòng: Pydantic)
- Repo: https://github.com/baro1chuo/FastAPI_LTHD
