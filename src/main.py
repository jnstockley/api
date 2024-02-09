from typing import Annotated

import toml
from fastapi import FastAPI, Header, HTTPException

import docker

app = FastAPI()


config = toml.load("config/application.toml")

api_key = config['API']['api_key']


@app.get("/docker/")
def get_latest_docker_version(docker_image: str = "", x_api_key: Annotated[str | None, Header()] = None):
    if x_api_key != api_key:
        raise HTTPException(status_code=401, detail="Unauthorized")
    image = docker_image.split(":")[0]
    latest_version = docker.get_latest_docker_image(image)
    return f"{image}:{latest_version}"
