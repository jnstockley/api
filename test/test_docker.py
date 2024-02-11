import os

from fastapi.testclient import TestClient

from src.main import app

client = TestClient(app)


def test_docker_no_auth():
    response = client.get("/docker")
    assert response.status_code == 422
    res_json = response.json()
    assert "detail" in res_json
    details = res_json["detail"]
    assert len(details) == 1
    detail = details[0]
    detail_type = detail["type"]
    loc = detail["loc"]
    msg = detail["msg"]
    detail_input = detail["input"]
    assert detail_type == "missing"
    assert len(loc) == 2
    assert msg == "Field required"
    assert detail_input is None
    assert "header" in loc
    assert "x-api-key" in loc


def test_docker_invalid_api_key_and_no_param():
    header = {"X-API-KEY": "hello-world-123"}
    response = client.get("/docker", headers=header)
    assert response.status_code == 401
    assert response.json() == {"detail": "Unauthorized"}


def test_docker_valid_api_key_and_no_param():
    api_key = os.environ["api_key"]
    header = {"X-API-KEY": api_key}
    response = client.get("/docker", headers=header)
    assert response.status_code == 422
    assert response.json() == {"detail": "Missing docker_image query parameter"}


def test_docker_valid_api_key_invalid_param():
    docker_image = "api"
    api_key = os.environ["api_key"]
    header = {"X-API-KEY": api_key}
    param = {"docker_image": docker_image}
    response = client.get("/docker", headers=header, params=param)
    assert response.status_code == 404
    assert response.json() == {"detail": f"{docker_image} not found in Docker Hub"}


def test_docker_valid_api_key_valid_param():
    docker_image = "adguard/adguardhome:v0.107.43"
    api_key = os.environ["api_key"]
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
