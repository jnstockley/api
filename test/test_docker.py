import os
from unittest import TestCase

from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


class TestDocker(TestCase):

    def test_docker_no_auth(self):
        mock_response = [
            {
                "type": "missing",
                "loc": ["header", "x-api-key"],
                "msg": "Field required",
                "input": None,
            },
            {
                "type": "missing",
                "loc": ["query", "docker_image"],
                "msg": "Field required",
                "input": None,
            },
        ]
        response = client.get("/docker")
        assert response.status_code == 422
        res_json = response.json()
        assert "detail" in res_json
        details = res_json["detail"]
        assert details == mock_response

    def test_docker_api_key_not_set(self):
        temp = os.environ["API_KEY"]
        os.environ["API_KEY"] = ""
        header = {"X-API-KEY": "hello-world-123"}
        response = client.get("/docker", headers=header)
        assert response.status_code == 500
        assert response.json() == {"detail": "API Key not set"}
        os.environ["API_KEY"] = temp

    def test_docker_invalid_api_key_and_no_param(self):
        header = {"X-API-KEY": "hello-world-123"}
        response = client.get("/docker", headers=header)
        assert response.status_code == 401
        assert response.json() == {"detail": "Unauthorized"}

    def test_docker_valid_api_key_and_no_param(self):
        api_key = os.environ["API_KEY"]
        header = {"X-API-KEY": api_key}
        mock_response = {
            "detail": [
                {
                    "type": "missing",
                    "loc": ["query", "docker_image"],
                    "msg": "Field required",
                    "input": None,
                }
            ]
        }
        response = client.get("/docker", headers=header)
        assert response.status_code == 422
        assert response.json() == mock_response

    def test_docker_valid_api_key_empty_param(self):
        docker_image = ""
        api_key = os.environ["API_KEY"]
        header = {"X-API-KEY": api_key}
        param = {"docker_image": docker_image}
        response = client.get("/docker", headers=header, params=param)
        assert response.status_code == 422
        assert response.json() == {"detail": "Missing docker_image query parameter"}

    def test_docker_valid_api_key_invalid_param(self):
        docker_image = "api"
        api_key = os.environ["API_KEY"]
        header = {"X-API-KEY": api_key}
        param = {"docker_image": docker_image}
        response = client.get("/docker", headers=header, params=param)
        assert response.status_code == 404
        assert response.json() == {"detail": f"{docker_image} not found in Docker Hub"}

    def test_docker_valid_api_key_valid_param(self):
        docker_image = "adguard/adguardhome:v0.107.43"
        api_key = os.environ["API_KEY"]
        header = {"X-API-KEY": api_key}
        param = {"docker_image": docker_image}
        response = client.get("/docker", headers=header, params=param)
        assert response.status_code == 200
        res_json = response.json()
        assert "image" in res_json
        assert "latest_image_version" in res_json
        assert "newer_version" in res_json
        assert docker_image.split(":")[0] in res_json["image"]
        assert res_json["newer_version"]
