include .env

default:help

help:
	@echo "make start"
	@echo "make refactor"
	@echo "make lint"
	@echo "make tests"
	@echo "make docker-up"
	@echo "make docker-build"
	@echo "make docker-down"
	@echo "make docker-destroy"
	@exit 0

start:
	PYTHONPATH=$(shell pwd):${PYTHONPATH} poetry run python src/bot.py

refactor:
	poetry run black ./
	poetry run isort ./

lint:
	poetry run black --check ./
	poetry run isort --check-only ./

tests:
	PYTHONPATH=$(shell pwd):${PYTHONPATH} python -m pytest -v --disable-warnings

docker-up:
	docker-compose up -d --remove-orphans

docker-build:
	docker-compose build

docker-down:
	docker-compose down

docker-destroy:
	docker-compose down -v --remove-orphans