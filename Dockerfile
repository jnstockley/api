FROM python:3.12.3-alpine3.19

RUN apk add alpine-sdk libffi-dev

ENV PATH="/root/.local/bin:$PATH"

RUN python3 -m pip install --user pipx

RUN pipx install poetry

RUN mkdir /opt/jstockley-api

COPY pyproject.toml /opt/jstockley-api

COPY poetry.lock /opt/jstockley-api

WORKDIR /opt/jstockley-api

RUN poetry install --without=test

COPY src/ /opt/jstockley-api

EXPOSE 5000

CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
