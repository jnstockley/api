from fastapi import APIRouter

router = APIRouter(
    prefix='/health-check'
)


@router.get("/")
async def read_users():
    return {"status": "ok"}
