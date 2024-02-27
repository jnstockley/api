import toml
from fastapi import FastAPI

from controllers import docker, health_check

version = toml.load("pyproject.toml")["tool"]["poetry"]["version"]

app = FastAPI(
    docs_url="/docs/swagger",
    redoc_url="/docs/redoc",
    title="Jnstockley API",
    version=version,
    contact={"name": "Jack Stockley"},
    license_info={"name": "MIT License", "url": "https://mit-license.org"},
)

app.include_router(health_check.router)
app.include_router(docker.router)
