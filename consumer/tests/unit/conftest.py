"""Pytest fixtures for consumer unit tests."""

from collections.abc import Generator

import pytest
import structlog

from common.message_queue.in_memory import InMemoryQueuePublisher
from common.models.queue import QueueMessage, QueueName
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


@pytest.fixture
def collect_messages(rmq_publisher: InMemoryQueuePublisher):
    """Return helper to get messages from in-memory CLICK_TRACKER queue."""

    def _collect() -> list[QueueMessage]:
        return list(rmq_publisher.queues[QueueName.CLICK_TRACKER])

    return _collect
