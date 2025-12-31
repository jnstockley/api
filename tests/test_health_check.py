import os
from unittest import TestCase

from fastapi.testclient import TestClient
from sqlmodel import Session, create_engine
from testcontainers.postgres import PostgresContainer

# Start postgres container and set DATABASE_URL before importing app
postgres = PostgresContainer("postgres:17-alpine").start()
DATABASE_URL = postgres.get_connection_url(driver="psycopg")
os.environ["DATABASE_URL"] = DATABASE_URL

# Now import app after DATABASE_URL is set
from src.database import get_db
from src.api import app

engine = create_engine(DATABASE_URL)
invalid_engine = create_engine(
    "postgresql+psycopg://postgres:postgres@postgres:5432/postgres2"
)

client = TestClient(app)


# Dependency to override the get_db dependency in the main app
def override_get_db():
    with Session(engine) as session:
        yield session


def override_invalid_db():
    with Session(invalid_engine) as session:
        yield session


app.dependency_overrides[get_db] = override_get_db


class TestHealthCheck(TestCase):
    def test_health_check(self):
        response = client.get("/health-check")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
