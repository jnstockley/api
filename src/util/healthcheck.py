import sys

<<<<<<< HEAD
from sqlalchemy import select

from database import get_db
=======
>>>>>>> external/main
from util.logging import logger


def healthcheck() -> bool:
<<<<<<< HEAD
    try:
        # get_db() is a generator, so we need to get the session from it
        db = next(get_db())
        # Execute a simple query to check the database connection
        db.exec(select(1))
        sys.exit(0)
    except Exception as e:  # noqa: BLE001
        logger.error(e)
        sys.exit(1)
=======
    logger.info("Healthcheck passed!")
    sys.exit(0)
>>>>>>> external/main
