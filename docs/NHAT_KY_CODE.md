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
