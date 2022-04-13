FROM python:3.10-slim-buster

WORKDIR /app

COPY pyproject.toml /app/src/pyproject.toml
RUN cd src/ && pip3 install poetry
RUN cd src/ && poetry config virtualenvs.create false
RUN cd src/ && poetry install --no-dev
COPY src/ /app/src/
