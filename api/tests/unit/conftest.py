"""Pytest fixtures for API unit tests: in-memory click repository override."""

import pytest

from api.app.app import app
from api.app.resource_factories import get_click_repository
from api.tests.conftest import logger
from common.repository.in_memory import InMemoryClickRepository


@pytest.fixture
def in_memory_click_repository():
    """Provide an in-memory click repository and override FastAPI dependency; clear on teardown."""
    repository = InMemoryClickRepository(logger)
    app.dependency_overrides[get_click_repository] = lambda: repository

    yield repository
    app.dependency_overrides.clear()
    repository.clear()
