import os
from unittest import TestCase
from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy.orm import sessionmaker
from testcontainers.postgres import PostgresContainer

import models
from database import engine, get_db
from src.api import app

postgres = PostgresContainer("postgres:17-alpine").start()

DATABASE_URL = postgres.get_connection_url(driver="psycopg")
os.environ["DATABASE_URL"] = DATABASE_URL

models.Base.metadata.create_all(bind=engine)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

client = TestClient(app)


def override_get_db():
    database = TestingSessionLocal()
    yield database
    database.close()


app.dependency_overrides[get_db] = override_get_db


class TestWebhook(TestCase):
    def setUp(self):
        os.environ["NEXTCLOUD_URL"] = "https://nextcloud.example.com"
        os.environ["NEXTCLOUD_TALK_TOKEN"] = "test-token"
        os.environ["NEXTCLOUD_TALK_SECRET"] = "test-secret"

    def test_missing_body(self):
        api_key = os.environ["API_KEY"]
        header = {"X-API-KEY": api_key}
        response = client.post("/webhook/databasus", headers=header, json={})
        assert response.status_code == 422

    def test_empty_header(self):
        api_key = os.environ["API_KEY"]
        header = {"X-API-KEY": api_key}
        response = client.post(
            "/webhook/databasus",
            headers=header,
            json={"header": "", "message": "hello"},
        )
        assert response.status_code == 422

    def test_empty_message(self):
        api_key = os.environ["API_KEY"]
        header = {"X-API-KEY": api_key}
        response = client.post(
            "/webhook/databasus",
            headers=header,
            json={"header": "title", "message": ""},
        )
        assert response.status_code == 422

    def test_not_configured(self):
        api_key = os.environ["API_KEY"]
        header = {"X-API-KEY": api_key}
        del os.environ["NEXTCLOUD_URL"]
        try:
            response = client.post(
                "/webhook/databasus",
                headers=header,
                json={"header": "title", "message": "hello"},
            )
            assert response.status_code == 500
        finally:
            os.environ["NEXTCLOUD_URL"] = "https://nextcloud.example.com"

    def test_insecure_url(self):
        api_key = os.environ["API_KEY"]
        header = {"X-API-KEY": api_key}
        os.environ["NEXTCLOUD_URL"] = "http://nextcloud.example.com"
        try:
            response = client.post(
                "/webhook/databasus",
                headers=header,
                json={"header": "title", "message": "hello"},
            )
            assert response.status_code == 500
        finally:
            os.environ["NEXTCLOUD_URL"] = "https://nextcloud.example.com"

    @patch("controllers.webhook.TalkMessenger.send", return_value=True)
    def test_send_message(self, mock_send):
        api_key = os.environ["API_KEY"]
        header = {"X-API-KEY": api_key}
        response = client.post(
            "/webhook/databasus",
            headers=header,
            json={"header": "title", "message": "hello"},
        )
        assert response.status_code == 200
        assert response.json() == {"status": "sent"}
        mock_send.assert_called_once_with("**title**\nhello")

    @patch("controllers.webhook.TalkMessenger.send", return_value=False)
    def test_send_message_failure(self, mock_send):
        api_key = os.environ["API_KEY"]
        header = {"X-API-KEY": api_key}
        response = client.post(
            "/webhook/databasus",
            headers=header,
            json={"header": "title", "message": "hello"},
        )
        assert response.status_code == 502

    def test_missing_api_key(self):
        response = client.post(
            "/webhook/databasus",
            json={"header": "title", "message": "hello"},
        )
        assert response.status_code in (401, 422)
