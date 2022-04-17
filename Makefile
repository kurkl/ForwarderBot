refactor:
	poetry run black ./
	poetry run isort ./

lint:
	poetry run black --check ./
	poetry run isort --check-only ./


up:
	docker-compose -f docker-compose-local.yml up -d

services:
	docker-compose -f docker-compose-local.yml up -d --force-recreate --remove-orphans db redis pgbouncer

down:
	docker-compose -f docker-compose-local.yml down

build:
	docker build -t awnulled/forwarder-bot/nginx -f docker/nginx/Dockerfile .
	docker build -t awnulled/forwarder-bot/app -f Dockerfile .
	docker build -t awnulled/forwarder-bot/pgbouncer -f docker/pgbouncer/Dockerfile .
	docker build -t awnulled/forwarder-bot/postgres -f docker/postgres/Dockerfile .

