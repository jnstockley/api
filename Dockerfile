FROM ghcr.io/astral-sh/uv:0.6.9-python3.13-alpine

RUN adduser -S app && \
    mkdir /app && \
    chown app /app

USER app

ADD . /app

WORKDIR /app

RUN export PYTHONPATH=/app/src:$PYTHONPATH && \
    uv sync --frozen --no-dev

EXPOSE 5000

HEALTHCHECK --interval=60s --timeout=10s --start-period=20s --retries=5 CMD curl --fail http://127.0.0.1:5000/health-check || exit 1

ENTRYPOINT ["uv", "run", "--frozen", "--directory", "src", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "5000", "--proxy-headers"]
