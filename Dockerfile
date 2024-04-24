FROM python:3.12.3-alpine3.19

RUN apk update

RUN apk upgrade

RUN apk add alpine-sdk libffi-dev

RUN curl -sSL https://install.python-poetry.org | python3 -

ENV PATH="/root/.local/bin:$PATH"

RUN mkdir /opt/jstockley-api

COPY pyproject.toml /opt/jstockley-api

COPY poetry.lock /opt/jstockley-api

WORKDIR /opt/jstockley-api

RUN poetry install --without=test

COPY src/ /opt/jstockley-api

EXPOSE 5000

CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
