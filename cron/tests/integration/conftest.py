"""Pytest fixtures for cron integration tests."""

import asyncio
from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
import structlog
from aio_pika import connect_robust

from common.message_queue.rmq_queue import RMQPublisher
from common.models.queue import QueueMessage, QueueName
from common.repository.sql import SQLClickRepository
from common.settings import rabbit_settings
from dbmodels.src.database import DatabaseConnection

# Import all fixtures from common tests
from common.tests.conftest import *  # noqa

logger = structlog.get_logger()


async def _purge_rmq_queue(url: str, queue_name: str) -> None:
    """Purge all messages from the given queue (queue must already exist)."""
    connection = await connect_robust(url)
    try:
        channel = await connection.channel()
        queue = await channel.get_queue(queue_name)
        await queue.purge()
    finally:
        await connection.close()


async def _collect_rmq_messages(
    url: str,
    queue_name: str,
    timeout_seconds: float = 2.0,
) -> list[QueueMessage]:
    """Consume messages from the queue for up to timeout_seconds and return parsed QueueMessages."""
    connection = await connect_robust(url)
    messages: list[QueueMessage] = []

    async def consume() -> None:
        channel = await connection.channel()
        queue = await channel.get_queue(queue_name)
        async with queue.iterator() as queue_iter:
            async for raw in queue_iter:
                async with raw.process():
                    messages.append(QueueMessage.model_validate_json(raw.body.decode()))

    try:
        await asyncio.wait_for(consume(), timeout=timeout_seconds)
    except asyncio.TimeoutError:
        pass
    finally:
        await connection.close()
    return messages


def _make_rmq_publisher() -> RMQPublisher:
    """Create RMQ publisher with queue names and exchange from settings."""
    queue_names = [name.value for name in QueueName]
    return RMQPublisher(
        url=rabbit_settings.rabbit_url,
        queue_names=queue_names,
        exchange_name=rabbit_settings.rabbit_exchange_name,
        channel_pool_size=2,
        connection_pool_size=1,
        exchange_type=rabbit_settings.rabbit_exchange_type,
        queue_type=rabbit_settings.rabbit_queue_type,
        delivery_limit=rabbit_settings.rabbit_delivery_limit,
    )


@pytest_asyncio.fixture
async def rmq_publisher() -> AsyncGenerator[RMQPublisher, None]:
    """RMQ publisher with exchange and queue declared; queue purged before each test."""
    publisher = _make_rmq_publisher()
    await publisher.declare_exchange_and_queue(
        rabbit_settings.rabbit_dead_letter_exchange_name,
    )
    await _purge_rmq_queue(rabbit_settings.rabbit_url, QueueName.CLICK_TRACKER.value)
    yield publisher


@pytest_asyncio.fixture
def click_repository(
    clear_db: None, db_connection: DatabaseConnection
) -> SQLClickRepository:
    """SQL click repository (DB cleared via clear_db when used)."""
    return SQLClickRepository(logger=logger, connection=db_connection)


@pytest.fixture
def collect_messages():
    """Return helper to consume messages from CLICK_TRACKER queue (for assertions)."""

    async def _collect(timeout_seconds: float = 2.0) -> list[QueueMessage]:
        return await _collect_rmq_messages(
            url=rabbit_settings.rabbit_url,
            queue_name=QueueName.CLICK_TRACKER.value,
            timeout_seconds=timeout_seconds,
        )

    return _collect
