DCOMPOSE=docker-compose
.PHONY: up
up:
	$(DCOMPOSE) up -d

.PHONY: up-empty-database
up-empty-database:
	$(DCOMPOSE) up -d database
	sleep 2

.PHONY: up-db_migration
up-db_migration:
	$(DCOMPOSE) up db_migration

.PHONY: up-apps
up-apps: up
	$(DCOMPOSE) up -d --profile apps

.PHONY: up-api
up-api:
	$(DCOMPOSE) up -d database
	@sleep 3
	$(DCOMPOSE) up db_migration
	$(DCOMPOSE) --profile apps up -d api

.PHONY: up-consumer
up-consumer: up
	$(DCOMPOSE) up -d consumer

.PHONY: up-cron
up-cron: up
	$(DCOMPOSE) up -d cron

.PHONY: down
down:
	$(DCOMPOSE) down

.PHONY: clean
clean:
	$(DCOMPOSE) down --volumes --remove-orphans

.PHONY: clean-deep
clean-deep:
	$(DCOMPOSE) down -v --rmi all --remove-orphans

.PHONY: pre-commit
pre-commit:
	pre-commit install --install-hooks
	pre-commit run --all-files

.PHONY: create-migration
create-migration:
	@if [ -z "$(name)" ]; then \
		echo "Error: name is not set. Use 'make create-migration name=\"name_of_version\"'"; \
		exit 1; \
	fi
	@(unset DB_URL)
	$(DCOMPOSE) down --volumes --remove-orphans
	$(DCOMPOSE) up -d database db_migration
	alembic -c dbmodels/alembic.ini revision --autogenerate -m "$(name)"
	pre-commit run ruff-format --files dbmodels/alembic/versions/$(name).py

.PHONY: migrate-db
migrate-db:
	@(unset DB_URL)
	alembic -c dbmodels/alembic.ini upgrade head

.PHONY: downgrade-db
downgrade-db:
	@(unset DB_URL)
	alembic -c dbmodels/alembic.ini downgrade -1


.PHONY: test-setup
test-setup:
	$(DCOMPOSE) down --volumes --remove-orphans
	$(DCOMPOSE) up -d database rabbitmq
	export ENVIRONMENT=test
	# Wait for the database and RabbitMQ to be ready
	@sleep 5

.PHONY: test-api
test-api: test-setup
	@echo "Running tests for API..."
	uv run python -m pytest -vv \
		--asyncio-mode=auto \
		--color=yes \
		--code-highlight=yes \
		--showlocals \
		--cov-config=.coveragerc \
		--cov-report term-missing \
		--cov=api ./api

.PHONY: test-consumer
test-consumer: test-setup
	@echo "Running tests for Consumer..."
	uv run python -m pytest -vv \
		--asyncio-mode=auto \
		--color=yes \
		--code-highlight=yes \
		--showlocals \
		--cov-config=.coveragerc \
		--cov-report term-missing \
		--cov=consumer ./consumer

.PHONY: test-cron
test-cron: test-setup
	@echo "Running tests for Cron..."
	uv run python -m pytest -vv \
		--asyncio-mode=auto \
		--color=yes \
		--code-highlight=yes \
		--showlocals \
		--cov-config=.coveragerc \
		--cov-report term-missing \
		--cov=cron ./cron

.PHONY: test-dbmodels
test-dbmodels: test-setup
	@echo "Running tests for DB Models..."
	uv run python -m pytest -vv \
		--asyncio-mode=auto \
		--color=yes \
		--code-highlight=yes \
		--showlocals \
		--cov-config=.coveragerc \
		--cov-report term-missing \
		--cov=dbmodels ./dbmodels

.PHONY: test-common
test-common: test-setup
	@echo "Running tests for Common..."
	uv run python -m pytest -vv \
		--asyncio-mode=auto \
		--color=yes \
		--code-highlight=yes \
		--showlocals \
		--cov-config=.coveragerc \
		--cov-report term-missing \
		--cov=common ./common

.PHONY: test
test: test-dbmodels test-api test-consumer test-cron test-common


.PHONY: upgrade-requirements
upgrade-requirements:
	uv sync --upgrade

.PHONY: install-requirements
install-requirements:
	uv venv
	uv sync

.PHONY: clean-test
clean-test:
	@echo "Cleaning up test resources..."
	$(DCOMPOSE) down --volumes --remove-orphans

# Load test: 1000 req/s for 60s (start API first: make up-api)
.PHONY: load-test
load-test:
	uv run --extra load locust -f locustfile.py --host http://localhost:8080 \
		--users 1000 --spawn-rate 1000 --run-time 60s --headless

# Load test with web UI (open http://localhost:8089 to control users and view stats)
.PHONY: load-test-ui
load-test-ui:
	uv run --extra load locust -f locustfile.py --host http://localhost:8080

.PHONY: help
help:
	@grep -E '^[a-zA-Z0-9 -]+:.*#'  Makefile | sort | while read -r l; do printf "\033[1;32m$$(echo $$l | cut -f 1 -d':')\033[00m:$$(echo $$l | cut -f 2- -d'#')\n"; done
