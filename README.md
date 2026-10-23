# ZooGuide – Backend FastAPI (Nhóm 9)

Backend tra cứu động vật sở thú đa ngôn ngữ: Guest xem/tìm/lọc động vật và đánh giá; User gửi và quản lý
đánh giá của mình; Admin quản lý động vật, tài khoản, đánh giá, thống kê và cài đặt.

Công nghệ: FastAPI · SQLAlchemy 2.0 (async, aiosqlite) · SQLite · Alembic · Pydantic v2 · JWT (PyJWT) · pytest.

## Chạy dự án

```bash
pip install -r requirements.txt
python -m alembic upgrade head            # tạo/cập nhật bảng trong app/database/zoo.db
python -m app.core.sample_data            # (tùy chọn) nạp dữ liệu mẫu
python -m uvicorn app.main:app --reload --ssl-keyfile certs/key.pem --ssl-certfile certs/cert.pem
```
Mở **https://127.0.0.1:8000/docs** (server chạy HTTPS, gọi bằng `http://` sẽ không được).

### Chứng chỉ HTTPS (làm 1 lần trên mỗi máy)
Thư mục `certs/` chứa khóa riêng nên **không** đưa lên git; mỗi người tự tạo bằng OpenSSL (có sẵn trong Git Bash và Codespaces):
```bash
mkdir -p certs
MSYS_NO_PATHCONV=1 openssl req -x509 -newkey rsa:2048 -nodes -sha256 -days 365 \
  -keyout certs/key.pem -out certs/cert.pem \
  -subj "/CN=localhost" -addext "subjectAltName=DNS:localhost,IP:127.0.0.1"
```
(`MSYS_NO_PATHCONV=1` chỉ cần trên Git Bash Windows; Linux/Codespaces bỏ đi cũng được.)

Đây là chứng chỉ **tự ký** (self-signed) để chạy trên máy, nên:
- Trình duyệt báo "Kết nối không riêng tư": bấm **Nâng cao → Tiếp tục truy cập 127.0.0.1** (1 lần).
- Postman: **Settings → General → tắt "SSL certificate verification"**, hoặc thêm `certs/cert.pem` ở **Settings → Certificates → CA Certificates**.
- curl: thêm `-k`, hoặc `--cacert certs/cert.pem`.
- Khi triển khai thật: dùng chứng chỉ do CA cấp (vd Let's Encrypt qua Nginx/Caddy); Codespaces đã có sẵn HTTPS ở link `https://...app.github.dev`.

- Sau mỗi lần `git pull`: chạy lại `pip install -r requirements.txt` rồi `python -m alembic upgrade head`.
- Dữ liệu mặc định (ngôn ngữ, vai trò, mức bảo tồn, nhóm động vật, cài đặt) do `app/core/seed.py` **tự thêm** mỗi lần khởi động.
- File CSDL `app/database/zoo.db` và thư mục `certs/` **không** đưa lên git; mỗi người tự tạo.
- Trên Windows nếu gõ `alembic` / `uvicorn` báo không tìm thấy lệnh thì dùng `python -m alembic`, `python -m uvicorn`.

### Tài khoản mẫu (sau khi chạy `sample_data`)
| Email | Vai trò | Mật khẩu |
|---|---|---|
| admin@zooguide.vn | Admin | 12345678 |
| an@zooguide.vn, binh@zooguide.vn, john@zooguide.vn, chau@zooguide.vn | User | 12345678 |

Chỉ dùng để demo, không dùng khi triển khai thật.

### Gọi API có đăng nhập trên /docs
1. `POST /api/auth/login` với email + mật khẩu, rồi copy giá trị `token`.
2. Bấm nút **Authorize** ở góc trên, dán token vào.
3. Gọi các API cần đăng nhập.

## Chạy test
```bash
python -m pytest -v
```
Mỗi test chạy trên một CSDL tạm, tạo bằng chính migration Alembic.

## Thay đổi cấu trúc bảng
1. Sửa model trong `app/models/`.
2. `python -m alembic revision --autogenerate -m "mô tả ngắn"`, rồi **đọc lại** file trong `alembic/versions/`. Đổi tên cột hoặc sửa CHECK thì tự viết bằng `op.batch_alter_table`.
3. `python -m alembic upgrade head`; thử `python -m alembic downgrade -1` rồi `upgrade head` lại.
4. Commit model và migration cùng nhau.

## Tài liệu
- `CLAUDE.md`: kiến trúc, quy ước code, đặc tả API bản chốt.
- `docs/NHAT_KY_CODE.md`: nhật ký từng bước code, kèm giải thích và minh chứng.
