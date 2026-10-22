import asyncio, time
from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI()


class Item(BaseModel):
    name: str = Field(min_length=1)
    price: float = Field(gt=0)


@app.post("/items", status_code=201)       # Bài A
def create_item(item: Item):
    return item


@app.get("/io-async")                      # Bài B, C1: đúng
async def io_async():
    await asyncio.sleep(0.1)               # mô phỏng chờ DB/HTTP
    return {"ok": True}


@app.get("/io-blocking-wrong")             # Bài C2: SAI
async def io_blocking_wrong():
    time.sleep(0.1)                        # chặn cả event loop
    return {"ok": True}


@app.get("/io-sync")                       # Bài C3: def thường
def io_sync():
    time.sleep(0.1)                        # chạy trong threadpool
    return {"ok": True}
