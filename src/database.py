import os
from typing import Annotated

from fastapi.params import Depends
from sqlalchemy.orm import declarative_base
from sqlmodel import Session, create_engine

SQLALCHEMY_DATABASE_URL = os.environ["DATABASE_URL"]

engine = create_engine(SQLALCHEMY_DATABASE_URL)

Base = declarative_base()


def get_db():
    with Session(engine) as session:
        yield session


db_dependency = Annotated[Session, Depends(get_db)]
