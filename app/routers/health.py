from fastapi import APIRouter

router = APIRouter(prefix="/api", tags=["Health"])

@router.get("/heath")
def health() -> dict:
    return {"status": "ok"}