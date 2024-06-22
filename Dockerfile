FROM python:3.12.4-alpine3.20

RUN apk update

RUN apk upgrade

RUN apk add alpine-sdk python3-dev libressl-dev musl-dev libffi-dev gcc libressl-dev curl

RUN adduser -g "api" api

USER api

ENV PATH="/root/.local/bin:$PATH"

RUN pip install --upgrade pip

RUN python3 -m pip install --user pipx

RUN pipx install poetry

RUN mkdir /opt/jstockley-api

COPY pyproject.toml /opt/jstockley-api

COPY poetry.lock /opt/jstockley-api

WORKDIR /opt/jstockley-api

RUN poetry install --without=test --no-root

USER root

RUN apk del alpine-sdk python3-dev libressl-dev musl-dev libffi-dev gcc libressl-dev

USER api

COPY src/ /opt/jstockley-api

EXPOSE 5000

HEALTHCHECK CMD curl --fail http://localhost:5000/health-check || exit 1

CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
