FROM python:3.12.4-alpine3.20

RUN apk update

RUN apk upgrade

RUN apk add alpine-sdk python3-dev libressl-dev musl-dev libffi-dev gcc libressl-dev curl

RUN addgroup -S api && adduser -S api -G api

USER api

ENV PATH="/home/api/.local/bin:$PATH"

RUN python3 -m pip install --upgrade pip

RUN python3 -m pip install --user pipx

RUN pipx install poetry

RUN mkdir /home/api/jnstockley-api

COPY pyproject.toml /home/api/jnstockley-api

COPY poetry.lock /home/api/jnstockley-api

WORKDIR /home/api/jnstockley-api

RUN poetry install --without=test --no-root

USER root

RUN apk del alpine-sdk python3-dev libressl-dev musl-dev libffi-dev gcc libressl-dev

USER api

COPY src/ /home/api/jnstockley-api

EXPOSE 5000

HEALTHCHECK --interval=60s --timeout=10s --start-period=20s --retries=5 CMD curl --fail http://127.0.0.1:5000/health-check || exit 1

CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
