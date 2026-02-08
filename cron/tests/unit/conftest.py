"""Pytest fixtures for cron tests."""

from collections.abc import Generator

import pytest
import structlog

from common.message_queue.in_memory import InMemoryQueuePublisher
from common.repository.in_memory import InMemoryClickRepository

logger = structlog.get_logger()


@pytest.fixture
def rmq_publisher() -> Generator[InMemoryQueuePublisher]:
    """In-memory queue publisher."""
    publisher = InMemoryQueuePublisher()
    publisher.clear()
    yield publisher
    publisher.clear()


@pytest.fixture
def click_repository() -> Generator[InMemoryClickRepository]:
    """In-memory click repository."""
    repository = InMemoryClickRepository(logger=logger)
    repository.clear()
    yield repository
    repository.clear()
