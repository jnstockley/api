FROM jnstockley/poetry:1.8.5-python3.13.1 AS build

RUN apk update && \
    apk upgrade && \
    apk add alpine-sdk python3-dev musl-dev libffi-dev gcc curl openssl-dev cargo pkgconfig && \
    mkdir /api

COPY pyproject.toml /api

COPY poetry.lock /api

WORKDIR /api

RUN poetry install --without=test --no-root

COPY src/ /api


FROM jnstockley/poetry:1.8.5-python3.13.1

RUN apk add curl

COPY --from=build /root/.cache/pypoetry/virtualenvs  /root/.cache/pypoetry/virtualenvs

COPY --from=build /api /api

WORKDIR /api

EXPOSE 5000

HEALTHCHECK --interval=60s --timeout=10s --start-period=20s --retries=5 CMD curl --fail http://127.0.0.1:5000/health-check || exit 1

CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
