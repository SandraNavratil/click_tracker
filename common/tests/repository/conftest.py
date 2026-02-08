"""Pytest fixtures for repository tests: in-memory click repository."""

import pytest
import structlog

from common.repository.in_memory import InMemoryClickRepository

logger = structlog.get_logger()


@pytest.fixture
def in_memory_click_repository() -> InMemoryClickRepository:
    """Return a fresh in-memory repository with cleared storage for each test."""
    repository = InMemoryClickRepository(logger)
    repository.clear()
    return repository
