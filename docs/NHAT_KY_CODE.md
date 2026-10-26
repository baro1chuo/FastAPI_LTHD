# Nhật ký code – Backend ZooGuide (branch `tong`)

Mỗi bước gồm: ngày, việc đã làm, giải thích, lệnh kiểm tra, điểm cần nhóm chốt. Dùng để đưa vào báo cáo.

---

## Trước Bước 0 – Tách model `identity.py` (22/10/2026)

**Việc đã làm:** tách `app/models/identity.py` thành `app/models/role.py` (bảng ROLE) và `app/models/user.py` (bảng USER); sửa import ở core, repository, service. Tên bảng và cột giữ nguyên nên CSDL không đổi. Commit: `Tách model identity thành role.py và user.py`.

---

## Bước 0 – Đưa Alembic vào quản lý cấu trúc bảng (22/10/2026)

### Việc đã làm
| File | Thay đổi |
|---|---|
| `alembic.ini`, `alembic/` | Tạo bằng `alembic init -t async alembic` (mẫu async). |
| `alembic/env.py` | Lấy URL từ `app/core/config.py` (đổi `sqlite:///` thành `sqlite+aiosqlite:///`), import đủ model, `target_metadata = Base.metadata`, bật `render_as_batch=True` ở cả 2 chế độ. |
| `alembic.ini` | Để trống `sqlalchemy.url`, ghi chú URL lấy từ `env.py`. |
| `app/core/database.py` | Bỏ `Base.metadata.create_all`; `init_db()` chỉ còn gọi `seed()`. CSDL chưa có bảng thì báo lỗi rõ ràng "hãy chạy alembic upgrade head". |
| `.gitignore` | Thêm `app/database/*.db`. |
| `app/database/zoo.db` | Gỡ khỏi git bằng `git rm --cached` (file trên máy vẫn còn). |
| `app/database/.gitkeep` | Giữ thư mục `app/database/` trong git để `alembic upgrade head` có chỗ tạo file CSDL sau khi clone. |
| `requirements.txt` | Thêm `alembic==1.20.1`, `aiosqlite==0.22.1`. |

### Giải thích
- **Migration** là "lịch sử thay đổi cấu trúc bảng" viết thành các file Python trong `alembic/versions/`. Mỗi file có `upgrade()` (áp thay đổi) và `downgrade()` (hoàn tác).
- Trước đây app gọi `Base.metadata.create_all`. Hàm này chỉ **tạo bảng còn thiếu**, không sửa được bảng đã có (thêm cột, đổi tên cột). Alembic giải quyết việc này, và giúp mọi thành viên có cùng cấu trúc bảng chỉ bằng `alembic upgrade head`.
- Alembic ghi phiên bản hiện tại của CSDL vào bảng `alembic_version`, nên biết cần chạy tiếp migration nào.
- `render_as_batch=True`: SQLite không hỗ trợ `ALTER COLUMN`, nên Alembic tạo bảng mới, chép dữ liệu sang rồi đổi tên.
- Dùng mẫu async ngay từ đầu (driver `aiosqlite`). Như vậy khi app chuyển sang async ở Bước 8 thì không phải sửa lại Alembic.

### Lệnh kiểm tra
```bash
pip install -r requirements.txt
python -m alembic current      # kết nối được CSDL; chưa có migration nên chưa in phiên bản
python -m alembic check        # trên CSDL trống: liệt kê đủ 15 bảng sẽ được tạo
```
- `alembic check` trên CSDL trống liệt kê đủ 15 bảng: category, conservation_status, language, role, zone, animal, category_translation, conservation_status_translation, system_settings, user, zone_translation, MAP_POINT, REVIEW, animal_translation, MAP_POINT_TRANSLATION.
- App chạy với `zoo.db` cũ: đăng nhập 200, `/api/animals` trả 18 động vật.
- App chạy với CSDL mới chưa có bảng: báo "CSDL chưa có bảng. Hãy chạy: alembic upgrade head".

### Điểm cần nhóm chốt
- Từ bước này, `zoo.db` **không còn trên git**. Mỗi người tự tạo bằng `alembic upgrade head` (sau Bước 1) rồi chạy app; dữ liệu mẫu nạp bằng `python -m app.core.sample_data`.
- Trên máy Windows nếu gõ `alembic` báo "command not found" thì dùng `python -m alembic ...`.

---

## Bước 1 – Đổi `featured` thành `available` (ẩn/hiện) + migration gốc (22/10/2026)

### Việc đã làm
| File | Thay đổi |
|---|---|
| `app/models/base.py` | Thêm `NAMING_CONVENTION` để mọi khóa chính/UNIQUE/khóa ngoại tự có tên (`pk_`, `uq_`, `fk_`); Alembic cần tên để sửa bảng ở chế độ batch. |
| `app/models/animal.py` | Cột `featured` thành `available` (mặc định 1 = hiển thị), CHECK `ck_animal_available`. |
| `app/schemas/animals.py` | Bỏ `featured`, thêm `available`. `AnimalUpdate` thành dạng **sửa một phần** cho PATCH; gửi `null` cho cột bắt buộc trả 422. |
| `app/repositories/animal_repository.py` | `list_animals(include_hidden=...)` lọc động vật ẩn; `list_related` chỉ lấy động vật đang hiện; `replace_translations` (PUT) thành `upsert_translations` (PATCH). |
| `app/services/animal_service.py` | Động vật ẩn trả 404 với khách; admin xem được; `update_animal` dùng `exclude_unset`; thêm `get_visible_animal`; DELETE ghi TODO chờ nhóm chốt. |
| `app/core/deps.py` | Thêm `get_optional_user` (không token = Guest) và `is_admin`. |
| `app/routers/animals.py` | Bỏ tham số `featured`; PUT thành **PATCH**; admin gửi token thì thấy cả động vật ẩn. |
| `app/services/review_service.py` | Gửi đánh giá cho động vật đang ẩn trả 404 (UC09 E3). |
| `app/core/sample_data.py` | Cột "nổi bật" thành "đang hiển thị"; Kỳ giông Mexico để **ẩn** làm ví dụ xóa mềm. |
| `alembic/versions/0c0490a1c7ab_init_schema.py` | Migration gốc tạo 15 bảng, có ghi chú từng bảng. |

### Giải thích
- **Xóa mềm** là không xóa dòng khỏi CSDL mà chỉ đổi `available = 0`. Động vật "biến mất" với khách nhưng admin vẫn thấy và hiện lại được. Xóa thật (DELETE) thì mất luôn bản dịch và đánh giá.
- API công khai trả **404** cho động vật đang ẩn (giống như không tồn tại), để khách không đoán được trong CSDL còn gì.
- **PATCH khác PUT:** PUT gửi đủ mọi trường để ghi đè; PATCH chỉ gửi trường cần đổi. Pydantic ghi lại trường nào client thật sự gửi (`model_fields_set`), và service lấy đúng các trường đó bằng `model_dump(exclude_unset=True)`.

Ví dụ ẩn một động vật (admin):
```http
PATCH /api/animals/1
Authorization: Bearer <token admin>
{"available": false}
```
```json
{"id": 1, "scientific_name": "Panthera tigris", "available": false, "zone_id": 1, "category_id": 1,
 "conservation_status_code": "EN", "popularity": 980, "image": null,
 "translations": [{"lang": "en", "name": "Tiger", "...": "..."}, {"lang": "vi", "name": "Hổ", "...": "..."}]}
```
Sau đó khách gọi `GET /api/animals/1` thì nhận `404 {"detail": "Không tìm thấy động vật"}`.

### Lệnh kiểm tra và minh chứng
```bash
rm app/database/zoo.db
python -m alembic upgrade head
python -m alembic downgrade -1 && python -m alembic upgrade head   # downgrade xóa sạch bảng, upgrade tạo lại
python -m alembic check        # "No new upgrade operations detected." = model khớp migration
python -m alembic current      # 0c0490a1c7ab (head)
python -m app.core.sample_data
```
`.schema animal` (máy không có lệnh `sqlite3` nên đọc bằng Python `sqlite3`; kết quả giống hệt):
```sql
CREATE TABLE animal (
	id INTEGER NOT NULL PRIMARY KEY AUTOINCREMENT,
	"scientificName" VARCHAR(150) NOT NULL,
	...
	available BOOLEAN DEFAULT 1 NOT NULL,
	CONSTRAINT ck_animal_available CHECK (available IN (0, 1)),
	CONSTRAINT ck_animal_popularity CHECK (popularity >= 0),
	CONSTRAINT "fk_animal_zoneId_zone" FOREIGN KEY("zoneId") REFERENCES zone (id) ON DELETE RESTRICT,
	CONSTRAINT "uq_animal_scientificName" UNIQUE ("scientificName")
)
```
`.schema REVIEW`:
```sql
CREATE TABLE "REVIEW" (
	...
	CONSTRAINT ck_review_rating CHECK (rating BETWEEN 1 AND 5),
	CONSTRAINT "fk_REVIEW_animalId_animal" FOREIGN KEY("animalId") REFERENCES animal (id) ON DELETE CASCADE,
	CONSTRAINT "fk_REVIEW_userId_user" FOREIGN KEY("userId") REFERENCES user (id) ON DELETE CASCADE,
	CONSTRAINT uq_review_animal_user UNIQUE ("animalId", "userId")
)
```
Kết quả gọi API sau khi nạp dữ liệu mẫu:
- Khách thấy 17 động vật, admin thấy 18 (cả Kỳ giông đang ẩn).
- Chi tiết động vật ẩn trả 404 với khách, 200 với admin; danh sách "liên quan" không có động vật ẩn.
- Đánh giá động vật ẩn trả 404.
- PATCH: ẩn/hiện, chỉ sửa `popularity`, chỉ sửa bản dịch `en` đều đúng. Lỗi trả đúng mã: `null` thành 422, khu vực không có thành 404, trùng tên thành 409, user thường thành 403. PUT trả 405.

### Điểm cần nhóm chốt
- DELETE `/api/animals/{id}` hiện vẫn **xóa thật** (kèm bản dịch, đánh giá), đã ghi TODO. Nhóm chốt: giữ, hay rút về khung.
- Admin gửi token khi gọi `GET /api/animals` và `GET /api/animals/{id}` thì thấy cả động vật ẩn. `/related` thì luôn chỉ có động vật đang hiện.

---

## Bước 2 – Đánh giá: UC12 sửa/xóa của tôi, tìm theo tên, kèm tên người viết / động vật (22/10/2026)

### Việc đã làm
| File | Thay đổi |
|---|---|
| `app/repositories/review_repository.py` | JOIN `user` + `animal` + bản dịch để trả `user_name`, `animal_name`; lọc thêm theo tên người viết (`user_name`) và chỉ động vật đang hiện (`visible_only`); thêm `get_with_names`. |
| `app/schemas/review.py` | `ReviewResponse` thêm `user_name`, `animal_name`. `ReviewUpdate` (UC12) bắt buộc gửi ít nhất 1 field, `rating` không được null. |
| `app/services/review_service.py` | Thêm `update_my_review`, `delete_my_review` (kiểm tra quyền sở hữu), `search_by_username`; đánh giá vừa sửa về `pending` (hoặc `approved` nếu bật tự duyệt); sửa docstring UC05 thành **UC04**. |
| `app/routers/review.py` | Thêm `PATCH`/`DELETE /api/reviews/me/{id}` và `GET /api/reviews/search?username=`; `GET /api/reviews` bắt buộc `animal_id`; nhận thêm `?lang=` để chọn ngôn ngữ tên động vật. |

### Giải thích
- **Quyền sở hữu (UC12):** server lấy `user_id` từ JWT, rồi so với `review.user_id`. Khác nhau trả **403**, nên user A không sửa được đánh giá của user B dù đoán được id.
- **Sửa xong phải duyệt lại:** nếu không, người dùng có thể sửa một đánh giá đã duyệt thành nội dung xấu mà vẫn hiện công khai.
- **JOIN để lấy tên:** bảng REVIEW chỉ lưu `userId` và `animalId`. Muốn hiện "Nguyễn Văn An đánh giá Hổ 5 sao" thì phải nối sang bảng `user` và `animal_translation`. Dùng LEFT JOIN cho bản dịch để động vật thiếu bản dịch vẫn ra được đánh giá.

Ví dụ sửa đánh giá của mình:
```http
PATCH /api/reviews/me/13
Authorization: Bearer <token của an@zooguide.vn>
{"comment": "Rất hay"}
```
```json
{"id": 13, "animal_id": 3, "animal_name": "Gấu ngựa", "user_id": 2, "user_name": "Nguyễn Văn An",
 "rating": 4, "comment": "Rất hay", "status": "pending", "created_at": "2026-10-22T16:20:11", "lang": "vi"}
```
Ví dụ admin tìm theo tên: `GET /api/reviews/search?username=bình` trả về `{"items": [...3 đánh giá của Trần Thị Bình...], "total": 3, "average": 3.3}`.

### Lệnh kiểm tra
Mở `/docs`: đăng nhập `an@zooguide.vn`, bấm Authorize, gửi `POST /api/reviews`, rồi `PATCH /api/reviews/me/{id}`. Sau đó đăng nhập `binh@zooguide.vn` và sửa đúng id đó: nhận 403.

Đã kiểm tra:
- Hổ có 3 đánh giá công khai, điểm trung bình 4.7, đủ tên người viết.
- Sửa của người khác trả 403; id không có trả 404; không token trả 401.
- `rating: 9`, body rỗng, `rating: null` đều trả 422.
- Sửa xong trạng thái về `pending`; đang bật tự duyệt thì về `approved`.
- Xóa xong gửi lại được.
- Tìm `bình` ra 3 đánh giá; user thường gọi `/search` trả 403.

### Điểm cần nhóm chốt
- Sửa/xóa đánh giá của người khác trả **403**, không phải 404. Đặc tả cho phép cả hai.
- `GET /api/reviews` giờ **bắt buộc** `animal_id` (theo đặc tả chốt) và bỏ lọc `user_id` công khai.
- Tìm theo tên không dấu ("binh" ra "Bình") chưa làm được, vì SQLite không bỏ dấu tiếng Việt.

---

## Bước 3 – Người dùng: đường dẫn mới, bỏ đổi vai trò, thêm `GET /me`, xóa `/test/all` (22/10/2026)

### Việc đã làm
| File | Thay đổi |
|---|---|
| `app/routers/user.py` | `PUT /update/me` thành **`PATCH /me`**; thêm **`GET /me`**; `PATCH /{id}` thành **`PATCH /{id}/status`**; **xóa** `GET /test/all` (đang lộ toàn bộ tài khoản không cần token). |
| `app/schemas/user.py` | `UserStatusUpdate` chỉ còn `status` (bỏ `role_id`); `UserResponse` thêm `created_at`; `full_name: null` trả 422. |
| `app/services/user_service.py` | `set_status` chỉ khóa/mở khóa; `update_profile` chỉ đổi field được gửi (gửi `avatar: null` thì xóa ảnh); docstring ghi UC và mã lỗi. |
| `app/repositories/user_repository.py` | Bỏ `get_role_by_id` (không còn đổi vai trò). |

### Giải thích
- **`/me` thay cho `/{id}`:** id lấy từ JWT, nên người dùng không thể đổi số trong URL để xem hoặc sửa hồ sơ người khác.
- **Khai báo `/me` trước `/{user_id}`:** FastAPI so đường dẫn theo thứ tự khai báo. Để sau thì "me" bị coi là `user_id` và trả 422.
- **Email không sửa được (UC08):** schema `UserProfileUpdate` không có trường email. Client có gửi `email` thì Pydantic bỏ qua.
- **Admin không tự khóa / tự xóa mình (UC14 E1):** tránh trường hợp hệ thống không còn admin nào.

Ví dụ:
```http
PATCH /api/users/me
Authorization: Bearer <token>
{"full_name": "An Nguyễn", "password": {"current_password": "12345678", "new_password": "newpass99", "confirm_password": "newpass99"}}
```
```json
{"full_name": "An Nguyễn", "email": "an@zooguide.vn", "avatar": null, "id": 2, "created_at": "2026-10-22T16:11:42"}
```
```http
PATCH /api/users/2/status          (token admin)
{"status": "locked"}
```
→ `200 {"id": 2, "status": "locked", ...}`. Sau đó user này đăng nhập nhận `403 {"detail": "Tài khoản đã bị khóa"}`.

### Lệnh kiểm tra
Mở `/docs` và thử lần lượt `GET /api/users/me`, `PATCH /api/users/me`, `PATCH /api/users/{id}/status`.

Đã kiểm tra:
- Đăng ký trùng email trả 409, mật khẩu ngắn trả 422.
- Gửi `email` trong PATCH thì bị bỏ qua; sai mật khẩu hiện tại trả 400; xác nhận không khớp trả 422.
- User thường gọi API admin trả 403. Admin tự khóa / tự xóa trả 403. Gửi `role_id` trả 422.
- Bị khóa thì đăng nhập và gọi `/me` đều trả 403. Mở khóa xong dùng lại được.
- Đường cũ: `PATCH /api/users/{id}` trả 405; `/test/all` không còn.

### Điểm cần nhóm chốt
- `GET /api/auth/me` và `GET /api/users/me` trả cùng dữ liệu. Giữ cả hai theo đặc tả chốt.
- `GET /api/users` vẫn trả mảng, chưa có `total` để phân trang. Thêm nếu frontend cần.

---

## Bước 4 – Systems (thống kê, cài đặt), khu vực, nhóm động vật, health (22/10/2026)

### Việc đã làm
| File | Thay đổi |
|---|---|
| `app/routers/systems.py` (đổi tên từ `admin.py`) | Đường dẫn đổi từ `/api/admin/...` thành **`/api/systems/...`**: `GET /dashboard`, `GET`/`PUT /settings`; mọi API yêu cầu Admin. Hết lỗi import `app.___`. |
| `app/schemas/systems.py` (đổi tên từ `admin.py`) | `DashboardOut` có số đánh giá theo trạng thái; `SettingsOut`/`SettingsUpdate` dùng đúng tên cột model; kiểm tra giờ mở cửa `07h00-17h00` (mở < đóng), định dạng hotline. |
| `app/repositories/stats_repository.py` (mới) | `count_all` (COUNT(*)), `count_reviews_by_status` (GROUP BY). |
| `app/services/stats_service.py`, `settings_service.py` (mới) | UC15 thống kê; UC16 cập nhật cài đặt, `default_lang` phải tồn tại và đang bật. |
| `app/routers/zone.py`, `schemas/zone.py`, `services/zone_service.py`, `repositories/zone_repository.py` | Chỉ còn `GET /api/zones` (đã bỏ thêm/sửa/xóa khu vực). |
| `app/routers/categories.py`, `schemas/category.py`, `services/category_service.py` (mới), `repositories/lookup_repository.py` | `GET /api/categories`. |
| `app/routers/health.py` | Sửa `/api/heath` thành `/api/health`. |
| `app/main.py` | Gắn đủ 8 router: health, auth, users, animals, reviews, zones, categories, systems. |

### Giải thích
- **GROUP BY:** đếm đánh giá theo trạng thái bằng 1 câu SQL (`SELECT status, COUNT(*) ... GROUP BY status`) thay vì 3 câu.
- **Cài đặt chỉ có 1 dòng:** bảng `system_settings` có CHECK `id = 1`. "Sửa cài đặt" là đổi dòng đó, không thêm dòng mới.
- **Bật tự duyệt không đổi đánh giá cũ (UC16):** `review_service` đọc cài đặt tại lúc gửi đánh giá, nên chỉ đánh giá gửi sau mới được duyệt ngay. Đánh giá đang chờ giữ nguyên.
- **Kiểm tra ở đâu:** định dạng giờ / hotline kiểm ở schema (sai trả 422); "ngôn ngữ có tồn tại không" phải tra CSDL nên kiểm ở service (sai trả 400).

Ví dụ:
```http
GET /api/systems/dashboard          (token admin)
```
```json
{"total_animals": 18, "total_zones": 6, "total_users": 5, "total_reviews": 12,
 "reviews_by_status": {"pending": 3, "approved": 8, "hidden": 1}}
```
```http
PUT /api/systems/settings           (token admin)
{"hotline": "1900 1234", "auto_approve": true}
```
```json
{"zoo_name": "ZooGuide", "open_hours": "07h00-17h00", "hotline": "1900 1234", "auto_approve": true, "default_lang": "vi"}
```
`GET /api/categories?lang=en` → `[{"id": 1, "code": "mammal", "name": "Mammals"}, ...]`

### Lệnh kiểm tra
Mở `/docs`, đăng nhập `admin@zooguide.vn`, bấm Authorize, rồi gọi `GET /api/systems/dashboard`, `PUT /api/systems/settings`.

Đã kiểm tra:
- Không token trả 401; user thường trả 403.
- Giờ `17h00-07h00`, `7h-17h`, `25h00-26h00`, hotline `abc`, `zoo_name` rỗng/null đều trả 422; `default_lang: "fr"` trả 400.
- Bật tự duyệt: đánh giá mới thành `approved`, 3 đánh giá `pending` cũ giữ nguyên.
- `/api/zones` trả 6 khu (thiếu bản dịch `en` thì dùng `vi`); `/api/categories` đổi ngôn ngữ đúng; `/api/health` trả `{"status": "ok"}`.

### Điểm cần nhóm chốt
- UC15 còn "động vật nhiều đánh giá nhất" và "lọc theo khoảng thời gian" **chưa làm**, vì đặc tả chốt chỉ yêu cầu 4 số liệu.
- "Khu mẫu" trong `seed.py` vẫn còn, nên có 6 khu vực. Bỏ dòng này nếu không cần.

---

## Bước 5 – Upload ảnh (multipart/form-data) cho người dùng và động vật (22/10/2026)

### Việc đã làm
| File | Thay đổi |
|---|---|
| `app/services/image_service.py` (mới) | `save_image`: chỉ nhận JPEG/PNG/WEBP/GIF, kiểm tra **chữ ký file** (không chỉ tin `content_type`), giới hạn 2 MB, đặt tên ngẫu nhiên bằng uuid, lưu vào `app/static/uploads/<thư mục>/`. |
| `app/services/user_service.py` | `upload_avatar`: chỉ đổi được ảnh của **chính mình** (id trên URL phải trùng id trong JWT). |
| `app/services/animal_service.py` | `upload_image` cho động vật (Admin). |
| `app/routers/user.py` | `POST /api/users/{user_id}/image`. |
| `app/routers/animals.py` | `POST /api/animals/{animal_id}/image`. |
| `app/main.py` | Mount `/static` để xem ảnh qua URL. |
| `app/core/config.py` | `STATIC_DIR`, `UPLOAD_DIR`, `MAX_IMAGE_BYTES` (đổi qua biến môi trường). |
| `.gitignore`, `requirements.txt` | Bỏ qua `app/static/uploads/`; thêm `python-multipart==0.0.32` (FastAPI cần thư viện này để đọc form-data). |

### Giải thích
- **multipart/form-data:** JSON chỉ chứa chữ, không gửi được file nhị phân. Form-data chia request thành nhiều "phần", mỗi phần là một trường hoặc một file. Vì vậy upload ảnh có endpoint riêng, còn các trường chữ vẫn gửi bằng JSON ở `PATCH`.
- **Vì sao kiểm tra chữ ký file:** `content_type` do client tự khai, có thể đặt `image/png` cho một file bất kỳ. Ảnh PNG thật luôn bắt đầu bằng các byte `89 50 4E 47...`, JPEG bằng `FF D8 FF`.
- **Vì sao đặt tên bằng uuid:** không dùng tên client gửi, tránh tên kiểu `../../main.py` ghi đè file của server, và hai người tải `avatar.png` không ghi đè lên nhau.
- CSDL chỉ lưu **đường dẫn** (`/static/uploads/avatars/xxx.png`), còn file nằm trên ổ đĩa.

Ví dụ (trong `/docs` có nút "Choose File"):
```http
POST /api/users/2/image
Authorization: Bearer <token của user id 2>
Content-Type: multipart/form-data; boundary=...
file = (avatar.png)
```
```json
{"full_name": "Nguyễn Văn An", "email": "an@zooguide.vn", "avatar": "/static/uploads/avatars/3f2a9c...e1.png", "id": 2, "created_at": "..."}
```
Mở `http://127.0.0.1:8000/static/uploads/avatars/3f2a9c...e1.png` là thấy ảnh.

### Lệnh kiểm tra
Đã kiểm tra:
- PNG/JPEG hợp lệ trả 200, xem được qua `/static`.
- Đổi ảnh người khác trả 403; không token trả 401.
- File `.txt` trả 400; file giả `image/png` trả 400; file WAV giả WEBP trả 400; ảnh > 2 MB trả 400; thiếu file trả 422.
- Ảnh động vật: user thường trả 403; động vật không có trả 404.

### Điểm cần nhóm chốt
- Ảnh cũ chưa bị xóa khi đổi ảnh mới (file cũ còn trên đĩa). Thêm bước dọn ảnh nếu cần.
- Giới hạn 2 MB và 4 định dạng là mình tự đặt; nhóm có thể đổi qua `MAX_IMAGE_BYTES`.

---

## Bước 6 – Đăng xuất `POST /api/auth/logout` (22/10/2026)

### Việc đã làm
| File | Thay đổi |
|---|---|
| `app/routers/auth.py` | Thêm `POST /api/auth/logout`: chỉ trả **204**, không đụng CSDL. |
| `app/core/deps.py` | Thêm `require_token`: chỉ kiểm tra JWT hợp lệ (401 nếu thiếu/sai), không tra bảng user. |
| `app/services/auth_service.py` | Sửa docstring: đăng xuất là **UC05** (bản chốt), không phải UC04. |

### Giải thích
- JWT là **stateless**: server không lưu danh sách token, chỉ kiểm tra chữ ký và hạn dùng. Vì vậy "đăng xuất" thật sự là frontend xóa token. API này chỉ để frontend báo cho server và nhận 204.
- **Hệ quả:** token đã cấp vẫn dùng được tới khi hết hạn (mặc định 24 giờ). Muốn thu hồi ngay thì phải lưu "danh sách token đã thu hồi" trong CSDL; đặc tả không yêu cầu nên chưa làm.

Ví dụ: `POST /api/auth/logout` với `Authorization: Bearer <token>` trả `204 No Content`, body rỗng. Không gửi token trả `401 {"detail": "Chưa đăng nhập"}`.

### Lệnh kiểm tra
Đã kiểm tra: user và admin đều trả 204; không token hoặc token sai trả 401; sau khi logout, token cũ vẫn gọi được `/api/users/me` (đúng với JWT stateless).

### Điểm cần nhóm chốt
- Giữ hay bỏ endpoint logout. Nó không thay đổi gì ở server.

---

## Bước 7 – Chạy lại toàn bộ + bộ test pytest (22/10/2026)

### Việc đã làm
| File | Thay đổi |
|---|---|
| `tests/conftest.py` | Mỗi test chạy trên CSDL tạm **riêng**: `alembic downgrade base` rồi `upgrade head` (tạo bảng đúng như migration), seed, nạp dữ liệu mẫu. Có sẵn fixture `admin`, `user`, `other_user` (header token) và `animal_ids`. Ảnh test ghi vào thư mục tạm. |
| `tests/test_auth.py` | 8 test: đăng ký, hash mật khẩu, trùng email, đăng nhập sai (cùng thông báo), tài khoản khóa, token giả, đăng xuất. |
| `tests/test_users.py` | 7 test: không sửa được email, đổi mật khẩu, avatar chỉ của mình, quyền admin, admin không tự khóa/xóa, bỏ đổi vai trò, xóa user xóa luôn đánh giá. |
| `tests/test_animals.py` | 9 test: khách chỉ thấy động vật hiện, tìm/lọc, chi tiết theo ngôn ngữ + ẩn → 404, liên quan, thêm/trùng, ẩn/hiện, PATCH một phần, xóa kéo theo đánh giá, upload ảnh. |
| `tests/test_reviews.py` | 9 test: UC04, UC09 (pending/409/tự duyệt/ẩn → 404/422), UC10, UC12 (sửa về pending, 403 với người khác, xóa rồi gửi lại), UC13. |
| `tests/test_systems.py` | 5 test: thống kê, kiểm tra cài đặt, bật tự duyệt không đổi pending, khu vực/nhóm theo ngôn ngữ, health. |
| `pytest.ini` | `pythonpath = .` để test import được `app`. |
| `requirements.txt` | Thêm `pytest`, `httpx` (TestClient cần httpx). |

### Giải thích
- **TestClient** gửi request thẳng vào app FastAPI trong bộ nhớ, không cần mở port. Chạy nhanh, và đi qua đủ router → service → repository → SQLite như request thật.
- **Mỗi test một CSDL sạch:** test A xóa động vật không làm test B sai. Test cũng dùng chính migration Alembic, nên nếu migration sai thì test hỏng ngay.
- Mỗi test có docstring ghi **quy tắc / UC** đang kiểm tra, để đối chiếu với đặc tả.

### Lệnh kiểm tra
```bash
python -m pytest -v
```
Kết quả: **38 passed** (khoảng 28 giây; phần lớn thời gian là băm mật khẩu PBKDF2 600.000 vòng).

Chạy server thật: `python -m uvicorn app.main:app`. `/api/health` trả `{"status":"ok"}`, `/docs` trả 200, và `openapi.json` liệt kê đủ **33 endpoint** đúng đặc tả chốt.

### Điểm cần nhóm chốt
- `pytest` và `httpx` chỉ dùng để chạy test. Nếu nhóm muốn tách riêng thì chuyển sang file `requirements-dev.txt`.

---

## Bước 8 – Hạ tầng async: engine, session, seed, khởi động app (22/10/2026)

### Việc đã làm
| File | Thay đổi |
|---|---|
| `app/core/config.py` | `DATABASE_URL` mặc định là `sqlite+aiosqlite:///./app/database/zoo.db`. |
| `app/core/database.py` | `create_async_engine`, `async_sessionmaker(expire_on_commit=False)`, bật `PRAGMA foreign_keys = ON` qua sự kiện `connect` trên `engine.sync_engine` (dùng cursor); `get_db` là async generator; `init_db` là async. |
| `app/core/seed.py` | `seed()` thành `async def`, mọi truy vấn đều `await`. |
| `app/core/sample_data.py` | `load_sample_data()` async; chạy từ dòng lệnh bằng `asyncio.run`, đóng kết nối trước khi thoát. |
| `app/main.py` | `lifespan`: `await init_db()` khi khởi động, `await engine.dispose()` khi tắt. |

### Giải thích
- **aiosqlite:** module `sqlite3` của Python là đồng bộ (chờ xong mới làm việc khác). `aiosqlite` chạy `sqlite3` trong một luồng riêng và trả kết quả qua `await`, nên event loop của FastAPI phục vụ được request khác trong lúc chờ đĩa.
- **`expire_on_commit=False`:** mặc định, sau `commit` SQLAlchemy "quên" giá trị các thuộc tính và tự truy vấn lại khi đọc. Với async, việc tự truy vấn ngầm này không chạy được (không có `await`) và ném lỗi **MissingGreenlet**, nên phải tắt.
- **PRAGMA qua `engine.sync_engine`:** engine async bọc bên trong một engine đồng bộ; sự kiện `connect` chỉ gắn được vào engine bên trong đó.
- **Trạng thái tạm:** sau bước này, các endpoint có dùng CSDL vẫn viết kiểu đồng bộ và sẽ được chuyển ở Bước 9. Bước này chưa có endpoint mới.

### Lệnh kiểm tra
```bash
python -m alembic current     # 0c0490a1c7ab (head): Alembic đọc được URL aiosqlite
python -m app.core.sample_data # chạy bằng async; CSDL đã đủ dữ liệu nên thêm 0
```
Kiểm tra bằng script: `PRAGMA foreign_keys` = **1**; truy vấn async đếm được 18 động vật; app khởi động (lifespan seed) và `/api/health` trả `{"status": "ok"}`.

---

## Bước 9 – Chuyển trọn chuỗi repository → service → router sang async (22/10/2026)

### Việc đã làm
Chuyển theo thứ tự nhóm, chạy test sau mỗi nhóm:

| Nhóm | File | Kết quả test sau khi chuyển |
|---|---|---|
| Users | `core/deps.py`, `repositories/user_repository.py`, `services/user_service.py`, `services/image_service.py`, `routers/user.py` | Chạy chung với Auth |
| Auth | `services/auth_service.py`, `routers/auth.py` | `test_auth` + `test_users`: 14/15 qua (1 test gọi API đánh giá, lúc đó chưa chuyển) |
| Animals | `services/i18n.py`, `repositories/settings_repository.py`, `lookup_repository.py`, `zone_repository.py`, `animal_repository.py`, `services/animal_service.py`, `routers/animals.py` | `test_animals`: 8/9 (1 test gọi API đánh giá) |
| Reviews | `repositories/review_repository.py`, `services/review_service.py`, `routers/review.py` | reviews + animals + users: 24/25 (1 test gọi API cài đặt) |
| Systems | `repositories/stats_repository.py`, `services/stats_service.py`, `settings_service.py`, `routers/systems.py` | |
| Zones/Categories | `services/zone_service.py`, `category_service.py`, `routers/zone.py`, `categories.py` | **Toàn bộ: 38/38 qua** |
| Test | `tests/conftest.py`, `tests/test_auth.py` | Nạp dữ liệu mẫu bằng `client.portal.call(...)`, tức chạy trong cùng event loop với app. |

Mọi truy vấn đều có `await`: `db.get`, `db.scalar`, `db.scalars`, `db.execute`, `db.flush`, `db.merge`, `db.delete`, `db.commit`, `db.refresh`. Riêng `db.add` / `db.add_all` chỉ đưa object vào session (chưa có I/O) nên không cần `await`.

### Giải thích
- **Async đúng chỗ:** chỉ hàm có I/O (chờ SQLite, đọc file upload) mới là `async def` và `await`. Hàm thuần không có I/O (`_to_item`, `_to_dict`, `_pick`, `_select_translated`, `_apply_filters`) giữ `def`. Biến chúng thành async chỉ thêm chi phí mà không được gì.
- **Không `asyncio.gather` trên cùng một session:** một `AsyncSession` chỉ chạy được 1 câu truy vấn tại một thời điểm. Ví dụ `get_dashboard` đếm 4 thứ, nhưng `await` lần lượt từng câu.
- **Tránh MissingGreenlet:** `User.role` dùng `lazy="joined"`, nên role được nạp cùng user trong 1 câu. Sau `commit`, đọc cột do CSDL tự điền (`created_at`) thì phải `await db.refresh(obj)` trước.
- **`require_admin`, `is_admin`, `require_token` giữ `def`:** chỉ so sánh vai trò / giải mã JWT, không có I/O.

### Lệnh kiểm tra
```bash
python -m pytest -q        # 38 passed
grep -rn "from sqlalchemy.orm import Session" app/repositories app/services app/routers   # không còn kết quả
```

### Điểm cần lưu ý
- Thời gian chạy test tăng từ khoảng 28 giây lên khoảng 97 giây, vì băm mật khẩu PBKDF2 (nặng CPU) đang chạy **thẳng trong event loop** và chặn mọi request khác trong lúc băm. Bước 10 xử lý việc này.

---

## Bước 10 – `run_in_threadpool` cho việc nặng CPU / ghi file (22/10/2026)

### Việc đã làm
| File | Thay đổi |
|---|---|
| `app/services/auth_service.py` | Đăng nhập: `await run_in_threadpool(verify_password, ...)`. |
| `app/services/user_service.py` | Đăng ký: băm mật khẩu qua threadpool. Đổi mật khẩu: cả kiểm tra mật khẩu cũ và băm mật khẩu mới đều qua threadpool. |
| `app/services/image_service.py` | Ghi file ảnh (`mkdir` + `write_bytes`) qua `run_in_threadpool(_write_file, ...)`. |
| `app/core/seed.py`, `app/core/sample_data.py` | Băm mật khẩu admin / tài khoản mẫu qua threadpool. |

`/api/health` và `/api/auth/logout` giữ `def`, không `await`: chúng không có I/O.

### Giải thích
- **Event loop chỉ có 1 luồng.** `await` giúp khi phải **chờ** (chờ SQLite, chờ mạng): trong lúc chờ, event loop đi phục vụ request khác. Nhưng PBKDF2 600.000 vòng là **tính toán**, không phải chờ: gọi thẳng trong `async def` thì event loop bận tính khoảng 0,3 giây và **mọi request khác phải đứng xếp hàng**. Đây là kiểu "async giả".
- `run_in_threadpool(f, *args)` chạy hàm đồng bộ `f` ở một luồng phụ, và `await` chờ kết quả. Event loop được giải phóng ngay. `hashlib` nhả GIL khi băm, nên nhiều lần băm còn chạy song song được trên nhiều nhân CPU.
- Ghi file bằng `Path.write_bytes` là I/O đồng bộ (chặn luồng tới khi ghi xong), nên cũng đưa vào threadpool.

### Minh chứng (đo trên server thật, `uvicorn`)
Gửi 5 request đăng nhập cùng lúc, trong lúc đó gọi `GET /api/health`:

| | `/api/health` phải chờ | 5 đăng nhập xong sau |
|---|---|---|
| **Trước** Bước 10 (gọi thẳng `verify_password`) | **183 ms** | 1,09 s |
| **Sau** Bước 10 (`run_in_threadpool`) | **5 ms** | 0,37 s |

Thời gian chạy bộ test cũng giảm từ khoảng 97 giây (sau Bước 9) xuống khoảng **28 giây**.

### Bảng: endpoint nào async, endpoint nào không, vì sao
| Endpoint | Kiểu | Lý do |
|---|---|---|
| `GET /api/health` | `def` | Không đụng CSDL hay file, không có gì để chờ. |
| `POST /api/auth/logout` | `def` | Chỉ giải mã JWT (HMAC rất nhanh), không đụng CSDL. |
| `POST /api/auth/register` | `async def` + threadpool | Chờ SQLite (kiểm tra email, INSERT) + băm mật khẩu nặng CPU qua `run_in_threadpool`. |
| `POST /api/auth/login` | `async def` + threadpool | Chờ SQLite tìm user + kiểm tra mật khẩu nặng CPU qua `run_in_threadpool`. |
| `GET /api/auth/me`, `GET /api/users/me` | `async def` | Dependency `get_current_user` chờ SQLite lấy user theo id trong JWT. |
| `PATCH /api/users/me` | `async def` + threadpool | Chờ SQLite; nếu có đổi mật khẩu thì kiểm tra / băm qua threadpool. |
| `POST /api/users/{id}/image`, `POST /api/animals/{id}/image` | `async def` + threadpool | `await upload.read()` chờ đọc file từ request; ghi file xuống đĩa qua threadpool; chờ SQLite lưu đường dẫn. |
| `GET/PATCH/DELETE /api/users...` (admin) | `async def` | Chờ SQLite. |
| Toàn bộ `/api/animals...` | `async def` | Chờ SQLite (danh sách, chi tiết, liên quan, thêm/sửa/xóa). |
| Toàn bộ `/api/reviews...` | `async def` | Chờ SQLite. |
| `GET /api/zones`, `GET /api/categories` | `async def` | Chờ SQLite. |
| `/api/systems/dashboard`, `/api/systems/settings` | `async def` | Chờ SQLite (các câu COUNT, đọc/ghi cài đặt). |

Hàm phụ **không** async dù nằm trong service/repository: `_to_item`, `_to_dict`, `_translations` (chỉ ghép dữ liệu đã có); `_select_translated`, `_select_with_names`, `_apply_filters` (chỉ **dựng** câu SQL, chưa chạy); `require_admin`, `is_admin` (chỉ so sánh vai trò).

### Lệnh kiểm tra
```bash
python -m pytest -q   # 38 passed (~28 giây)
```

---

## Kết thúc – Tổng kết (22/10/2026)

**Cập nhật tài liệu:**
- `CLAUDE.md` theo bản chốt: UC12 là "Sửa/xóa đánh giá của tôi"; UC04 Xem đánh giá / UC05 Đăng xuất; cột `available`; async; Alembic; đặc tả API mới, đường dẫn `/api/systems`.
- Tạo `README.md`: cách chạy, tài khoản mẫu, chạy test, quy trình thêm migration.

**Kiểm tra cuối** (làm giống một thành viên mới pull về):
```bash
rm app/database/zoo.db
python -m alembic upgrade head    # tạo 15 bảng
python -m alembic check           # No new upgrade operations detected.
python -m app.core.sample_data    # 5 khu vực, 18 động vật, 5 tài khoản, 12 đánh giá
python -m uvicorn app.main:app    # /api/health trả {"status":"ok"}
python -m pytest -q               # 38 passed
```

**Trạng thái endpoint:** đủ 33 endpoint theo đặc tả chốt đã chạy và có test. Các điểm còn TODO / cần nhóm chốt:

| Điểm | Hiện trạng |
|---|---|
| Xóa thật động vật (`DELETE /api/animals/{id}`) | Đang xóa thật kèm bản dịch + đánh giá, có ghi TODO. Nhóm chốt: giữ, hay rút về khung. |
| `POST /api/auth/logout` | Chỉ trả 204, không thay đổi gì ở server. Giữ hay bỏ? |
| UC15: "động vật nhiều đánh giá nhất", "lọc theo khoảng thời gian" | Chưa làm (đặc tả chốt chỉ yêu cầu 4 số liệu). |
| Phân trang `GET /api/users` | Trả mảng, chưa có `total`. |
| Ảnh cũ khi đổi ảnh mới | File cũ chưa bị xóa khỏi đĩa. |
| "Khu mẫu" trong `seed.py` | Vẫn tạo khi CSDL chưa có khu nào, nên có 6 khu vực. |
| Tìm tên không dấu ("ho" ra "Hổ") | Chưa hỗ trợ (SQLite không bỏ dấu tiếng Việt). |
