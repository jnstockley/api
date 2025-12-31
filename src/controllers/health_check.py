from fastapi import APIRouter, HTTPException
from sqlalchemy import text

from database import db_dependency
from util.logging import logger

router = APIRouter(prefix="/health-check")


@router.get("/")
async def health_check(db: db_dependency):
    try:
        # Execute a simple query to check the database connection
        db.execute(text("SELECT 1"))
        return {"status": "ok"}
    except Exception as e:
        logger.error(e)
        raise HTTPException(status_code=500, detail="Database connection failed")
