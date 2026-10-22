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
