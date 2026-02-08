"""Entry point for running the Click Tracker cron."""

import asyncio
import sys

from common.message_queue.rmq_queue import RMQPublisher
from common.models.queue import QueueName
from common.repository.sql import SQLClickRepository
from common.settings import app_settings, rabbit_settings
from cron.app import logger
from cron.app.cronjob import run_cronjob
from dbmodels.src.database import DatabaseConnection
from dbmodels.src.settings import settings as db_settings

db_connection = DatabaseConnection(settings=db_settings, debug=app_settings.debug)
rmq_publisher = RMQPublisher(
    url=rabbit_settings.rabbit_url,
    exchange_name=rabbit_settings.rabbit_exchange_name,
    queue_names=[QueueName.CLICK_TRACKER],
    exchange_type=rabbit_settings.rabbit_exchange_type,
    queue_type=rabbit_settings.rabbit_queue_type,
    delivery_limit=rabbit_settings.rabbit_delivery_limit,
)


async def _initialize_rmq() -> None:
    """Declare exchange and queues so the cron can publish."""
    await rmq_publisher.declare_exchange_and_queue(
        dead_letter_exchange=rabbit_settings.rabbit_dead_letter_exchange_name,
    )


async def run_cron() -> None:
    """Run the cron job."""
    await _initialize_rmq()
    await run_cronjob(
        repository=SQLClickRepository(logger=logger, connection=db_connection),
        rmq_publisher=rmq_publisher,
    )


def main() -> None:
    """Main entry point for running the cron job."""
    try:
        asyncio.run(run_cron())
    except Exception:
        logger.exception("run_cronjob.failed")
        sys.exit(1)


if __name__ == "__main__":
    main()
