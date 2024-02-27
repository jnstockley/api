from fastapi import APIRouter

router = APIRouter(prefix="/health-check")


@router.get("/")
async def health_check():
    return {"status": "ok"}
