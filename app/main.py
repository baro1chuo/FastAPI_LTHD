from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import admin, animals, auth, health, review, user, zone

app = FastAPI(title="Zoo API", version="0.1.0")

# TODO: đưa danh sách origin vào core/config.py (đọc từ .env)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

for module in (health, auth, user, animals, zone, review, admin):
    app.include_router(module.router)
