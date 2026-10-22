"""Điểm vào của backend ZooGuide: tạo app FastAPI, bật CORS, đổi lỗi nghiệp vụ thành HTTP, gắn các router."""
from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.core.database import init_db
from app.core.exceptions import AppError
from app.routers import animals, auth, categories, health, review, systems, user, zone


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Chạy một lần khi khởi động: thêm dữ liệu mặc định còn thiếu (bảng do Alembic tạo trước)."""
    init_db()
    yield


app = FastAPI(title="Zoo API", version="0.1.0", lifespan=lifespan)

# TODO: đưa danh sách origin vào core/config.py (đọc từ .env)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(AppError)
async def app_error_handler(request: Request, exc: AppError):
    """Đổi exception nghiệp vụ từ service thành HTTP response {"detail": "..."} với mã lỗi tương ứng."""
    return JSONResponse(status_code=exc.status_code, content={"detail": exc.message})


for module in (health, auth, user, animals, review, zone, categories, systems):
    app.include_router(module.router)
