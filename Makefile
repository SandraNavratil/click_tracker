DCOMPOSE=docker-compose
# Bring up all services
.PHONY: up
up:
	$(DCOMPOSE) up -d

# Bring up all services
.PHONY: up-empty-database
up-empty-database:
	$(DCOMPOSE) up -d database
	sleep 2

.PHONY: up-db_migration
up-db_migration:
	$(DCOMPOSE) up db_migration

# Bring up specific profiles (e.g., app services)
.PHONY: up-apps
up-apps: up
	$(DCOMPOSE) up -d --profile apps

.PHONY: up-api
up-api: up
	$(DCOMPOSE) up -d api

.PHONY: up-consumer
up-consumer: up
	$(DCOMPOSE) up -d consumer

.PHONY: up-cron
up-cron: up
	$(DCOMPOSE) up -d cron

# Take down all services
.PHONY: down
down:
	$(DCOMPOSE) down

# Clean up services by stopping and removing containers, networks, images, and volumes
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

# Database migration(s)
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
test-setup:	# Set up test resources
	$(DCOMPOSE) down --volumes --remove-orphans
	$(DCOMPOSE) up -d database
	export ENVIRONMENT=test
	# Wait for the database to be fully ready
	@sleep 3

.PHONY: test-api
test-api: test-setup # Run tests for API
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
test-consumer: test-setup	# Run tests for Consumer
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
test-cron: test-setup	# Run tests for Cron
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
test-dbmodels: test-setup	# Run tests for DB Models
	@echo "Running tests for DB Models..."
	uv run python -m pytest -vv \
		--asyncio-mode=auto \
		--color=yes \
		--code-highlight=yes \
		--showlocals \
		--cov-config=.coveragerc \
		--cov-report term-missing \
		--cov=dbmodels ./dbmodels

.PHONY: test
test: test-dbmodels test-api test-consumer test-cron	# Run all tests


.PHONY: upgrade-requirements
upgrade-requirements:	# Upgrade requirements files
	uv sync --upgrade

.PHONY: install-requirements
install-requirements:	# Install requirements
	uv venv
	uv sync

.PHONY: clean-test
clean-test:	# Clean up test resources
	@echo "Cleaning up test resources..."
	$(DCOMPOSE) down --volumes --remove-orphans

.PHONY: help
help: # Shows help to all the commands
	@grep -E '^[a-zA-Z0-9 -]+:.*#'  Makefile | sort | while read -r l; do printf "\033[1;32m$$(echo $$l | cut -f 1 -d':')\033[00m:$$(echo $$l | cut -f 2- -d'#')\n"; done
