FROM jnstockley/poetry:1.8.3-python3.12.6

USER root

RUN mkdir /api

RUN chown -R python3:python3 /api

USER python3

COPY pyproject.toml /api

COPY poetry.lock /api

WORKDIR /api

RUN poetry install --without=test --no-root

COPY src/ /api

EXPOSE 5000

HEALTHCHECK --interval=60s --timeout=10s --start-period=20s --retries=5 CMD curl --fail http://127.0.0.1:5000/health-check || exit 1

CMD ["poetry", "run", "uvicorn", "main:app", "--host", "0.0.0.0", "--port", "5000"]
