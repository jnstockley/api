from unittest import TestCase

from fastapi.testclient import TestClient

from src.api import app

client = TestClient(app)


class TestHealthCheck(TestCase):

    def test_health_check(self):
        response = client.get("/health-check")
        assert response.status_code == 200
        assert response.json() == {"status": "ok"}
