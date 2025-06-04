FROM python:3.13.4-alpine

ARG VERSION=0.0.0.dev

RUN adduser -S app && \
    mkdir /app && \
    chown app /app
USER app

WORKDIR /app

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

COPY . /app

RUN sed -i "s/^version = .*/version = \"${VERSION}\"/" /app/pyproject.toml

RUN uv sync --frozen --no-cache

ENV PATH=/app/.venv/bin:$PATH
ENV PYTHONPATH=src

HEALTHCHECK --interval=60s --timeout=10s --start-period=20s --retries=5 CMD wget -nv -t 1 --spider http://127.0.0.1:5000/health-check || exit 1

CMD ["fastapi", "run", "src/api.py", "--port", "5000", "--host", "0.0.0.0"]
