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
