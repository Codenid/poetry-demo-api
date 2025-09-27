FROM python:3.10.14-slim

RUN apt-get update && apt-get install -y curl build-essential libpq-dev

RUN curl -sSL https://install.python-poetry.org | python3 - && \
    ln -s /root/.local/bin/poetry /usr/local/bin/poetry

WORKDIR /app

COPY pyproject.toml poetry.lock README.md ./
COPY ./src ./src

RUN poetry config virtualenvs.create false && \
    poetry check && \
    poetry install --no-interaction --no-ansi

EXPOSE 8000

CMD ["uvicorn", "poetry_demo.main:app", "--host", "0.0.0.0", "--port", "8000"]