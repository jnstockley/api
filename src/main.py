import os
from typing import Annotated
from fastapi import FastAPI, Header, HTTPException

from util import docker

app = FastAPI()

api_key = os.environ['api_key']


@app.get("/docker/")
def get_latest_docker_version(docker_image: str = "", x_api_key: Annotated[str | None, Header()] = None):
    if api_key is None or api_key == ''.strip():
        raise HTTPException(status_code=500, detail="API Key not set")
    if x_api_key != api_key:
        raise HTTPException(status_code=401, detail="Unauthorized")
    image = docker_image.split(":")[0]
    latest_version = docker.get_latest_docker_image(image)
    return f"{image}:{latest_version}"
