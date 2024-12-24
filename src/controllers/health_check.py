from fastapi import APIRouter, HTTPException

from database import db_dependency

router = APIRouter(prefix="/health-check")


@router.get("/")
async def health_check(db: db_dependency):
    try:
        # Execute a simple query to check the database connection
        db.execute("SELECT 1")
        return {"status": "ok"}
    except Exception:
        raise HTTPException(status_code=500, detail="Database connection failed")
