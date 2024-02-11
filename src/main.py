from fastapi import FastAPI

from controllers import docker, health_check

app = FastAPI()

app.include_router(health_check.router)
app.include_router(docker.router)
