FROM python:3.13-slim

RUN mkdir /app
WORKDIR /app

RUN apt-get update -yqq && apt-get install -yqq curl gcc libpq-dev

# Install uv package manager
COPY --from=ghcr.io/astral-sh/uv:latest /uv /bin/uv
COPY uv.lock /app/uv.lock
COPY pyproject.toml /app/pyproject.toml

ENV UV_PROJECT_ENVIRONMENT=/usr/local
ENV UV_LINK_MODE=copy

RUN   uv sync --frozen --all-groups

ARG INSTALL_TEST_DEPS=0
RUN if [ "$INSTALL_TEST_DEPS" = "1" ]; then uv sync --frozen --all-extras; fi

ARG package_version
ENV PACKAGE_VERSION=$package_version
ENV DD_VERSION=$PACKAGE_VERSION

LABEL name=click_tracker

COPY cron/run.py ./run_cron.py
COPY consumer/run.py ./run_consumer.py

COPY dbmodels ./dbmodels/
COPY common ./common/
COPY api ./api/
COPY consumer ./consumer
COPY cron ./cron
