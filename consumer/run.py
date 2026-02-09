"""Entry point for running the Click Tracker consumer."""

import asyncio
from common.message_queue.rmq_queue import RMQConsumer
from common.models.queue import QueueName
from common.settings import rabbit_settings
from consumer.app.rmq_entrypoint import handle_incoming_message

if __name__ == "__main__":
    consumer = RMQConsumer(
        callback=handle_incoming_message,
        queue_name=QueueName.CLICK_TRACKER,
        url=rabbit_settings.rabbit_url,
        exchange_name=rabbit_settings.rabbit_exchange_name,
        dead_letter_exchange=rabbit_settings.rabbit_dead_letter_exchange_name,
    )
    asyncio.run(consumer.consume())
