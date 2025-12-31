from sqlalchemy import text

from database import get_db, SessionLocal
from util.logging import logger


def healthcheck() -> bool:
    try:
        db = SessionLocal()
        # Execute a simple query to check the database connection
        db.execute(text("SELECT 1"))
        exit(0)
    except Exception as e:
        logger.error(e)
        exit(1)

