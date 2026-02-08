# Click Tracker

## Overview

### Top-level flow

1. **[API](#api)**
   Receives incoming click traffic, creates or uses a user, stores the click with `processing_state='new'`, and responds to the client.

2. **[Cron](#workers)**
   Periodically selects users with `processing_state='new'`, updates them to `processing_state='queued'`, and publishes messages to the queue.

3. **[Consumer](#workers)**
   Consumes messages from the queue, fetches external data from an external API, then updates the database with that data and sets `processing_state='done'`.

![Architecture and workflow](docs/flow_diagram.png)

### Contents

- [Installing requirements](#installing-requirements)
- [Development](#development) (Docker, Makefile, migrations)
- [Data model](#data-model)
- [Contributing](#contributing)
- [API](#api)
- [Workers](#workers) (Consumer, Cron)
- [Tests](#tests)
- [Load testing](#load-testing)

---

### Project structure

| Directory   | Purpose |
|------------|---------|
| `api/`     | HTTP API (FastAPI): click endpoints, docs. |
| `consumer/`| Worker that consumes the queue and enriches user data. |
| `cron/`    | Scheduled job that finds new users and publishes to the queue. |
| `common/`  | Shared code: models, repository abstractions, message queue. |
| `dbmodels/`| SQLAlchemy models and Alembic migrations. |

---

# Installing requirements

The project uses [uv](https://docs.astral.sh/uv) to manage Python versions and dependencies. Install `uv`:

```shell
curl -LsSf https://astral.sh/uv/install.sh | sh
```

or

```shell
brew install uv
```

Then create a virtual env and install dependencies:

```shell
uv venv
uv sync
```

For **development** (running tests, load tests), install optional extras:

```shell
uv sync --extra test        # pytest, factories, etc.
uv sync --extra load        # locust (load testing)
uv sync --all-extras       # test + load
```

The environment is created in the top-level `.venv` folder. Use `source .venv/bin/activate` to activate it, or run commands with `uv run ...` so the venv is used automatically.

- Add a dependency: `uv add <package>`
- Remove: `uv remove <package>`
- Upgrade all: `uv sync --upgrade`

Run a script with the venv: `uv run python script.py` or `uv run python -m script`

---

# Development

Services for local development are defined in `docker-compose.yml`. You need Docker (e.g. via Colima) installed.

Create a `.docker.env` file with the configuration needed by the apps, for example:

```dotenv
DB_URL=postgresql+asyncpg://user:password@database:5432/click_tracker
RMQ_URL=amqp://guest:guest@rabbitmq:5672/
ENVIRONMENT=local
```

Use the **Makefile** for common tasks.

### Makefile usage

#### Services

- `make up` — Start all services (database, RabbitMQ).
- `make up-empty-database` — Start only the database.
- `make up-db_migration` — Run database and migrations (docker compose up db_migration).
- `make up-apps` — Start all services including API, consumer, and cron (profile `apps`).
- `make up-api` — Start API (and dependencies).
- `make up-consumer` — Start consumer (and dependencies).
- `make up-cron` — Start cron (and dependencies).
- `make down` — Stop all services.

#### Cleanup

- `make clean` — Stop and remove containers, networks, and volumes.
- `make clean-deep` — Same as above and remove all images.
- `make clean-test` — Clean up test resources.

#### Pre-commit

- `make pre-commit` — Install and run pre-commit hooks.

#### Database migrations

- `make create-migration name="migration_name"` — Create a new migration (requires `name`). Brings up database and db_migration, then runs alembic autogenerate.
- `make migrate-db` — Apply migrations to the local DB (runs alembic upgrade head; ensure DB is running and `DB_URL` is unset or set for your local DB).
- `make downgrade-db` — Roll back the last migration on the local DB.

#### Testing

- `make test-setup` — Start database for tests.
- `make test-api` — Run API tests (with coverage).
- `make test-consumer` — Run consumer tests.
- `make test-cron` — Run cron tests.
- `make test-dbmodels` — Run dbmodels tests.
- `make test` — Run all tests.

#### Other

- `make install-requirements` — Create venv and run `uv sync`.
- `make upgrade-requirements` — Run `uv sync --upgrade`.
- `make help` — List Makefile targets with descriptions.

---

# Data model

![Data model](docs/erd.png)


**DB implementation:** SQLAlchemy models and Alembic migrations live under `dbmodels/`.

---

# Contributing

- Check [dbmodels/CHANGELOG.md](dbmodels/CHANGELOG.md) for existing versions and migrations.

### 1) Update models

- Edit [dbmodels/src/models.py](dbmodels/src/models.py).

### 2) Add or update tests

- Add/update tests for models and relations under `dbmodels/tests/` (and for api, consumer, cron as needed).

### 3) Update VERSION and CHANGELOG

- Bump [dbmodels/VERSION](dbmodels/VERSION).
- Update [dbmodels/CHANGELOG.md](dbmodels/CHANGELOG.md).

### 4) Create and apply migration

- Create: `make create-migration name="v_X_Y_Z"` (or your migration name).
- Apply locally: `make migrate-db` (with local DB running; ensure `DB_URL` is unset or set for your local DB).
- Roll back: `make downgrade-db` if needed.

---

# API

For local development you can run the API via `api/run.py` (e.g. from your IDE or from the project root):

```shell
uv run python api/run.py
```

Or with uvicorn directly:

```shell
uv run uvicorn --reload --host 0.0.0.0 --port 8080 api.app.app:app
```

### Environment variables

- `DB_URL=postgresql+asyncpg://user:password@localhost:5432/click_tracker`
- `RMQ_URL=amqp://guest:guest@localhost:5672`

---

# Workers

**Consumer** and **Cron** run as separate processes.

Each has a `run.py` in its directory (`consumer/`, `cron/`). Run from the project root, e.g.:

```shell
uv run python consumer/run.py
uv run python cron/run.py
```

### Environment variables

- `DB_URL=postgresql+asyncpg://user:password@localhost:5432/click_tracker`
- `RMQ_URL=amqp://guest:guest@localhost:5672`

---

# Tests

Set (or ensure) these for running tests:

- `DB_URL=postgresql+asyncpg://user:password@localhost:5432/click_tracker` (or the test DB URL used by docker-compose)
- `RMQ_URL=amqp://guest:guest@localhost:5672`
- `ENVIRONMENT=test`

Run all tests with coverage:

```shell
make test
```

Run per app:

```shell
make test-api
make test-consumer
make test-cron
make test-dbmodels
make test-common
```

# Load testing

Load tests use [Locust](https://locust.io/). Install the `load` extra: `uv sync --extra load`.

- **Headless** (e.g. 1000 users, 60s):
  `make load-test`
  (Start the API first: `make up-api`.)

- **Web UI** (interactive, stats at http://localhost:8089):
  `make load-test-ui`
