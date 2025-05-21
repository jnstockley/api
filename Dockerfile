FROM ghcr.io/astral-sh/uv:0.7.6-python3.13-alpine AS build

WORKDIR /app

COPY ./pyproject.toml .
COPY ./uv.lock .

RUN uv sync --frozen --no-dev

FROM python:3.13.3-alpine

RUN adduser -S app && \
    mkdir /app && \
    chown app /app
USER app

WORKDIR /app

COPY /src src
COPY --from=build /app/.venv .venv

EXPOSE 5000

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONPATH="/app/src"

HEALTHCHECK --interval=60s --timeout=10s --start-period=20s --retries=5 CMD wget -nv -t 1 --spider http://127.0.0.1:5000/health-check || exit 1

ENTRYPOINT ["uvicorn", "src.api:app", "--log-level", "info", "--host", "0.0.0.0" , "--port", "5000", "--proxy-headers"]
