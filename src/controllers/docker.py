from fastapi import APIRouter, Depends

from util import docker
from util.auth import get_token_header

router = APIRouter(
    prefix='/docker',
    dependencies=[Depends(get_token_header)]
)


@router.get("/")
async def get_latest_docker_version(docker_image: str = ""):
    image = docker_image.split(":")[0]
    latest_version = docker.get_latest_docker_image(image)
    return f"{image}:{latest_version}"
