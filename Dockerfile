FROM jnstockley/poetry:2.1.0-python3.13.2 AS build

RUN apk update && \
    apk upgrade && \
    apk add alpine-sdk python3-dev musl-dev libffi-dev gcc curl openssl-dev cargo pkgconfig && \
    mkdir /api

COPY . /api

WORKDIR /api

RUN poetry lock && \
    poetry check && \
    poetry install --without=dev

FROM jnstockley/poetry:2.1.0-python3.13.2
ARG VERSION=dev

RUN apk add curl

COPY --from=build /root/.cache/pypoetry/virtualenvs  /root/.cache/pypoetry/virtualenvs

COPY --from=build /api /api

WORKDIR /api

EXPOSE 5000

HEALTHCHECK --interval=60s --timeout=10s --start-period=20s --retries=5 CMD curl --fail http://127.0.0.1:5000/health-check || exit 1

ENV VERSION=${VERSION}

ENTRYPOINT ["poetry", "run", "uvicorn", "api:app", "--host", "0.0.0.0", "--port", "5000", "--proxy-headers"]
