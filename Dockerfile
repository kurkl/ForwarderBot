FROM python:3.8-slim-buster

ENV PYTHONPATH "${PYTHONPATH}:/app"

WORKDIR /app

COPY pyproject.toml /app/
RUN pip3 install poetry
RUN poetry config virtualenvs.create false
RUN poetry install --no-dev
EXPOSE 80
ADD . /app/
