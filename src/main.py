from fastapi import FastAPI

from controllers import health_check, docker

app = FastAPI()

app.include_router(health_check.router)
app.include_router(docker.router)
