# ZooGuide – Backend FastAPI

## Bài toán
Khách sở thú không biết nên xem con gì, ở khu nào; bảng giới thiệu ngắn, một ngôn ngữ, khó cập nhật.
Ban quản lý sửa thông tin và thu ý kiến khách thủ công. ZooGuide cho:
- **Guest**: tra cứu/lọc động vật (tên, nhóm, khu vực), xem chi tiết, động vật liên quan, đánh giá đã duyệt; nội dung đa ngôn ngữ.
- **User** (đã đăng nhập, kế thừa Guest): đăng ký/đăng nhập, sửa hồ sơ, đổi mật khẩu, gửi đánh giá, xem đánh giá của mình (mọi trạng thái).
- **Admin**: quản lý động vật, khu vực, tài khoản (khóa/mở khóa/xóa); duyệt/ẩn/xóa đánh giá; thống kê; cài đặt hệ thống.
- Ngoài phạm vi hiện tại: bản đồ & tuyến tham quan (bảng MAP_POINT có sẵn nhưng làm sau), QR, chatbot, yêu thích.

## Kiến trúc & thư mục
Router → Dependency (xác thực/phân quyền) → Service → Model (SQLAlchemy) → CSDL SQLite.
```
app/
  main.py        tạo app, CORS, include router
  core/          (chưa có) config.py, database.py (get_db), security.py (hash, JWT), deps.py (get_current_user, require_admin), exceptions.py
  models/        SQLAlchemy 2.0 – bảng theo ERD. Thuộc tính Python snake_case, tên cột DB camelCase (vd zone_id -> "zoneId")
  schemas/       Pydantic v2 – dữ liệu vào/ra API; common.py chứa kiểu dùng chung
  routers/       mỗi file = 1 nhóm trong bảng Đặc tả API; router mỏng, chỉ gọi service
  services/      (chưa có) logic nghiệp vụ: animal, zone, review, user, auth, stats, settings
test_schemas.py  self-check schema: `python test_schemas.py`
docs/zooguide_schema.sql   CSDL SQLite tham khảo đầy đủ ràng buộc (dựng từ ERD)
```

## Quy ước code
- Router không chứa logic nghiệp vụ, không query DB trực tiếp; gọi `services/*`.
- Service raise exception nghiệp vụ (NotFound 404, Conflict 409, Forbidden 403, Auth 401, BusinessRule 400); main.py đổi sang HTTP.
- Validation kiểu/định dạng đặt ở Pydantic (lỗi 422); kiểm tra cần tra DB (trùng email, còn động vật…) đặt ở service.
- Mọi đường dẫn bắt đầu bằng `/api`. Auth bằng JWT: `Authorization: Bearer <token>`.
- Ngôn ngữ: frontend gửi `lang`; GET dùng query `?lang=vi`, POST/PUT gửi trong body. Thiếu bản dịch -> dùng `defaultLang` trong SYSTEM_SETTINGS.
- SQLite: luôn bật `PRAGMA foreign_keys = ON` mỗi kết nối.
- Không thêm thư viện mới nếu stdlib/thư viện sẵn có làm được. Code tối giản.
- Branch: mỗi thành viên làm trên branch riêng (bao, tong, …), PR vào `main`.

## CSDL (ERD draw.io Trang-1)
LANGUAGE(code PK, name, isActive) · ROLE(id, code∈admin/staff/user, name)
USER(id, fullName, email UK, passwordHash, roleId FK RESTRICT, status∈active/locked, createdAt, avatar)
ZONE(id, color #RRGGBB, openHours "07h00-17h00", areaM2>0, image) · ZONE_TRANSLATION(zoneId+lang PK, name, description; UNIQUE(lang,name))
CATEGORY(id, code UK) · CATEGORY_TRANSLATION(categoryId+lang PK, name)
CONSERVATION_STATUS(code∈EX,EW,CR,EN,VU,NT,LC,DD,NE, color) · CONSERVATION_STATUS_TRANSLATION
ANIMAL(id, scientificName UK, zoneId FK RESTRICT, categoryId FK RESTRICT, conservationStatusCode FK RESTRICT, featured, popularity>=0, image)
ANIMAL_TRANSLATION(animalId+lang PK, name, appearance, distribution, ecology, behaviour, diet, reproduction, lifespan, ecologicalRole, threat; UNIQUE(lang,name))
REVIEW(id, animalId FK CASCADE, userId FK CASCADE, rating 1–5, comment ≤500, status∈pending/approved/hidden, createdAt, lang; UNIQUE(animalId,userId))
MAP_POINT / MAP_POINT_TRANSLATION (làm sau) · SYSTEM_SETTINGS(id=1, zooName, openHours, hotline, autoApprove, defaultLang)

## Quy tắc nghiệp vụ
- Mỗi user chỉ đánh giá 1 lần / động vật. Đánh giá mới: `approved` nếu autoApprove bật, ngược lại `pending`. Bật autoApprove không đổi các đánh giá đang pending.
- Khách chỉ thấy đánh giá `approved`; chủ đánh giá thấy mọi trạng thái của mình.
- Mật khẩu ≥ 8 ký tự (chỉ lưu hash); email duy nhất, không sửa được; tài khoản `locked` không đăng nhập được (403).
- Admin không được tự khóa/tự xóa chính mình.
- Không xóa khu vực còn động vật (409). Xóa động vật -> xóa luôn đánh giá & bản dịch.

## Use case (UC01–UC16)
UC01 Xem/tìm/lọc động vật · UC02 Chi tiết · UC03 Động vật liên quan (extend UC02) · UC04 Đăng xuất (frontend xóa token)
UC05 Xem đánh giá · UC06 Đăng ký · UC07 Đăng nhập · UC08 Hồ sơ · UC09 Gửi đánh giá · UC10 Đánh giá của tôi
UC11 QL động vật · UC12 QL khu vực · UC13 Duyệt/ẩn/xóa đánh giá · UC14 QL tài khoản · UC15 Thống kê · UC16 Cài đặt

## Đặc tả API
| Method | Path | Quyền | Chức năng |
|---|---|---|---|
| GET | /api/health | Công khai | Kiểm tra backend |
| GET | /api/animals | Công khai | Danh sách; lọc search, category, zone, sort, featured; phân trang |
| GET | /api/animals/{id} | Công khai | Chi tiết |
| GET | /api/animals/{id}/related | Công khai | Liên quan (cùng nhóm/khu), `limit` |
| POST / PUT / DELETE | /api/animals[/{id}] | Admin | Tạo / ghi đè / xóa (kèm đánh giá) |
| GET | /api/zones, /api/zones/{id} | Công khai | Danh sách / chi tiết |
| POST / PUT / DELETE | /api/zones[/{id}] | Admin | Tạo / sửa / xóa (409 nếu còn động vật) |
| POST | /api/auth/register, /api/auth/login | Công khai | Đăng ký / đăng nhập (trả JWT) |
| GET | /api/auth/me | User | User hiện tại |
| PUT | /api/users/update/me | User | Sửa hồ sơ, đổi mật khẩu |
| GET / GET / PATCH / DELETE | /api/users[/{id}] | Admin | Danh sách / chi tiết / khóa-mở-đổi vai trò / xóa |
| GET | /api/reviews | Công khai, lọc | Theo animal_id, user_id, status |
| POST | /api/reviews | User | Tạo đánh giá (user_id lấy từ token) |
| PATCH / DELETE | /api/reviews/{id} | Admin | Duyệt-ẩn / xóa |
| GET | /api/admin/dashboard | Admin | Thống kê |
| GET / PUT | /api/admin/settings | Admin | Đọc / cập nhật cài đặt |


## Tài liệu nhóm
- Báo cáo (Google Doc "LTHD NHÓM 9"): https://docs.google.com/document/d/1D2VkbSZJ0xYTjXR2LUkZ8l2m3XdChxIHU7TzBBVB_l0/edit
  (tab: User story và Use case, Activity Diagram, Đặc tả API, Database, Tầng Service, Sơ đồ tổ chức thư mục)
- ERD draw.io: https://drive.google.com/file/d/1gQ2U_159n-Bvh6iDDu_rNBc_nQSOCbWR/view
- Phân công: https://docs.google.com/spreadsheets/d/1ir71b6yCG4L3-9vFsDNO07OXZhSECIr20L8xxuKaz3o/edit
  (Hùng: tầng CSDL · Bảo: router · Tòng: service, activity diagram · Bảo+Tòng: Pydantic)
- Repo: https://github.com/baro1chuo/FastAPI_LTHD
