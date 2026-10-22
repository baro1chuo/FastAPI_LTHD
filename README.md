# ZooGuide – Backend FastAPI (Nhóm 9)

Backend tra cứu động vật sở thú đa ngôn ngữ: Guest xem/tìm/lọc động vật và đánh giá; User gửi và quản lý
đánh giá của mình; Admin quản lý động vật, tài khoản, đánh giá, thống kê và cài đặt.

Công nghệ: FastAPI · SQLAlchemy 2.0 (async, aiosqlite) · SQLite · Alembic · Pydantic v2 · JWT (PyJWT) · pytest.

## Chạy dự án

```bash
pip install -r requirements.txt
python -m alembic upgrade head            # tạo/cập nhật bảng trong app/database/zoo.db
python -m app.core.sample_data            # (tùy chọn) nạp dữ liệu mẫu
python -m uvicorn app.main:app --reload   # mở http://127.0.0.1:8000/docs
```

- Sau mỗi lần `git pull`: chạy lại `pip install -r requirements.txt` rồi `python -m alembic upgrade head`.
- Dữ liệu mặc định (ngôn ngữ, vai trò, mức bảo tồn, nhóm động vật, cài đặt) do `app/core/seed.py` **tự thêm** mỗi lần khởi động.
- File CSDL `app/database/zoo.db` **không** đưa lên git; mỗi người tự tạo bằng 2 lệnh trên.
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
