import os
from contextlib import asynccontextmanager

from fastapi import FastAPI

import models
from controllers import docker, health_check, ip
from database import engine

version = os.environ["VERSION"]

app = FastAPI(
    docs_url="/docs/swagger",
    redoc_url="/docs/redoc",
    title="Jnstockley API",
    version=version,
    contact={"name": "Jack Stockley"},
    license_info={"name": "MIT License", "url": "https://mit-license.org"},
)

@asynccontextmanager
async def lifespan():
    models.Base.metadata.create_all(bind=engine)

app.include_router(health_check.router)
app.include_router(docker.router)
app.include_router(ip.router)
