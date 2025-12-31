from sqlalchemy import select

from database import get_db
from util.logging import logger


def healthcheck() -> bool:
    try:
        # get_db() is a generator, so we need to get the session from it
        db = next(get_db())
        # Execute a simple query to check the database connection
        db.exec(select(1))
        exit(0)
    except Exception as e:
        logger.error(e)
        exit(1)

