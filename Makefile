include .env

default:help


start:
	PYTHONPATH=$(shell pwd):${PYTHONPATH} poetry run python src/bot.py

refactor:
	poetry run black ./
	poetry run isort ./

lint:
	poetry run black --check ./
	poetry run isort --check-only ./


docker-up:
	docker-compose up -d --remove-orphans

docker-build:
	docker-compose build

docker-down:
	docker-compose down

docker-destroy:
	docker-compose down -v --remove-orphans