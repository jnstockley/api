FROM ghcr.io/astral-sh/uv:0.6.6-python3.13-alpine

ADD . /app

WORKDIR /app

RUN uv sync --frozen --no-dev

ENTRYPOINT ["uv", "run", "--directory", "src", "main.py"]
