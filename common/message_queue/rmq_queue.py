"""RMQ queue publisher and consumer."""

import asyncio
from collections.abc import Callable, Coroutine
from functools import partial
from typing import override

import aio_pika
import structlog
from aio_pika import connect_robust
from aio_pika.abc import (
    AbstractChannel,
    AbstractIncomingMessage,
    AbstractRobustConnection,
    DeliveryMode,
)
from aio_pika.pool import Pool

from common.message_queue.abstract import AbstractQueueConsumer, AbstractQueuePublisher
from common.models.queue import QueueMessage, QueueName

publisher_logger = structlog.get_logger("RMQPublisher")
consumer_logger = structlog.get_logger("RMQConsumer")


class RMQPublisher(AbstractQueuePublisher):
    """Client that enables connection to AMQP server and publish messages asynchronously."""

    def __init__(
        self,
        url: str,
        queue_names: list[str],
        exchange_name: str,
        *,
        channel_pool_size: int = 20,
        connection_pool_size: int = 5,
        exchange_type: str = "direct",
        queue_type: str = "quorum",
        delivery_limit: int = 3,
    ):
        """Initialize the RMQ queue publisher.

        Args:
            url: AMQP connection URL.
            queue_names: Names of queues to declare and publish to.
            exchange_name: Name of the exchange.
            channel_pool_size: Max size of the channel pool.
            connection_pool_size: Max size of the connection pool.
            exchange_type: Exchange type (e.g. "direct").
            queue_type: Queue type (e.g. "quorum") for main and DLQ queues.
            delivery_limit: Max redeliveries before a message is sent to the DLQ.
        """
        self.exchange_name = exchange_name
        self.exchange_type = exchange_type
        self.queue_names = queue_names
        self.url = url
        self.queue_type = queue_type
        self.delivery_limit = delivery_limit
        self.connection_pool: Pool[aio_pika.RobustConnection] = Pool(
            partial(self._get_connection, url=url), max_size=connection_pool_size
        )
        self.channel_pool: Pool[aio_pika.Channel] = Pool(
            self._get_channel, max_size=channel_pool_size
        )

    @staticmethod
    async def _get_connection(url: str) -> AbstractRobustConnection:
        """Factory for robust connection to AMQP server.

        Args:
            url: URL address to connect to.

        Returns:
            AbstractRobustConnection: New robust connection to AMQP server.
        """
        return await aio_pika.connect_robust(url)

    async def _get_channel(self) -> AbstractChannel:
        """Factory for RMQ channels using connection pool (abstraction of RMQ channel).

        Returns:
            AbstractChannel: New channel connection.
        """
        async with self.connection_pool.acquire() as connection:
            return await connection.channel(publisher_confirms=True)

    async def publish(self, message: QueueMessage, queue: QueueName) -> None:
        """Publish message as JSON to the queue. The queue must be bound to the exchange.

        Args:
            message: Queue message to be serialized and sent.
            queue: Queue to publish to (QueueName enum).
        """
        async with self.channel_pool.acquire() as channel:
            exchange = await channel.get_exchange(self.exchange_name)
            await exchange.publish(
                aio_pika.Message(
                    message.model_dump_json().encode("utf-8"),
                    delivery_mode=DeliveryMode.PERSISTENT,
                ),
                queue,
            )

    async def declare_exchange_and_queue(self, dead_letter_exchange: str) -> None:
        """Declare an exchange and queues for this RMQPublisher.

        Args:
            dead_letter_exchange: Name of the dead-letter exchange.
        """
        connection = await connect_robust(self.url)
        channel = await connection.channel()
        exchange = await channel.declare_exchange(
            name=self.exchange_name,
            type=self.exchange_type,
            durable=True,
        )
        publisher_logger.info(
            "RMQPublisher.declare_exchange_and_queue.declare_exchange",
            name=self.exchange_name,
            type=self.exchange_type,
            durable=True,
        )
        await channel.declare_exchange(
            name=dead_letter_exchange,
            type=self.exchange_type,
            durable=True,
        )
        publisher_logger.info(
            "RMQPublisher.declare_exchange_and_queue.dead_letter_exchange",
            name=dead_letter_exchange,
            type=self.exchange_type,
            durable=True,
        )
        for queue_name in self.queue_names:
            queue = await channel.declare_queue(
                name=queue_name,
                durable=True,
                arguments={
                    "x-queue-type": self.queue_type,
                    "x-dead-letter-exchange": dead_letter_exchange,
                    "x-delivery-limit": self.delivery_limit,
                },
            )
            publisher_logger.info(
                "RMQPublisher.declare_exchange_and_queue.declare_queue",
                name=queue_name,
                arguments={
                    "x-queue-type": self.queue_type,
                    "x-dead-letter-exchange": dead_letter_exchange,
                    "x-delivery-limit": self.delivery_limit,
                },
                durable=True,
            )
            await queue.bind(exchange, queue_name)
            publisher_logger.info(
                "RMQPublisher.declare_exchange_and_queue.bind_queue_to_exchange",
                queue=queue_name,
                exchange=self.exchange_name,
            )

            dlq_queue_name = f"{queue_name}-dlq"
            dlq_queue = await channel.declare_queue(
                dlq_queue_name,
                arguments={"x-queue-type": self.queue_type},
                durable=True,
            )
            publisher_logger.info(
                "RMQPublisher.declare_exchange_and_queue.declare_dlq_queue",
                name=dlq_queue_name,
                arguments={"x-queue-type": self.queue_type},
                durable=True,
            )
            await dlq_queue.bind(dead_letter_exchange, routing_key=queue_name)
            publisher_logger.info(
                "RMQPublisher.declare_exchange_and_queue.bind_dlq_to_exchange",
                dlq_queue=dlq_queue_name,
                dlq_exchange=dead_letter_exchange,
            )

        await channel.close()
        publisher_logger.info("RMQPublisher.declare_exchange_and_queue.channel_closed")

    async def ping(self) -> None:
        """Ping the queue to check if it is alive."""
        async with self.channel_pool.acquire() as channel:
            for queue_name in self.queue_names:
                await channel.declare_queue(
                    queue_name,
                    durable=True,
                    passive=True,
                )


class RMQConsumer(AbstractQueueConsumer):
    """RMQ queue consumer."""

    def __init__(  # noqa: PLR0913 (too-many-arguments)
        self,
        callback: Callable[[AbstractIncomingMessage], Coroutine[None, None, None]],
        queue_name: QueueName,
        url: str,
        exchange_name: str,
        dead_letter_exchange: str,
        *,
        prefetch_count: int = 3,
        x_queue_type: str = "quorum",
        durable_queue: bool = True,
        x_delivery_limit: int = 3,
    ) -> None:
        """Initialize RMQConsumer with callback and queue name.

        Args:
            callback: Function to be called when a message is received.
            queue_name: Name of the queue to consume from.
            url: AMQP connection URL.
            exchange_name: Name of the exchange.
            dead_letter_exchange: Name of the dead-letter exchange.
            prefetch_count: QoS prefetch count, default 3.
            x_queue_type: Queue type, default "quorum".
            durable_queue: Whether the queue is durable, default True.
            x_delivery_limit: Delivery limit for the queue, default 3.
        """
        super().__init__(callback, queue_name)
        self.url = url
        self.durable_queue = durable_queue
        self.prefetch_count = prefetch_count
        self.exchange_name = exchange_name
        self.dead_letter_exchange = dead_letter_exchange
        self.arguments = {
            "x-queue-type": x_queue_type,
            "x-dead-letter-exchange": dead_letter_exchange,
            "x-delivery-limit": x_delivery_limit,
        }

    @override
    async def consume(self) -> None:
        """Consume messages from the queue."""
        connection = await connect_robust(self.url)
        consumer_logger.debug("RMQConsumer.consume.connect_robust")
        channel = await connection.channel()
        consumer_logger.debug("RMQConsumer.consume.channel_created")
        await channel.set_qos(prefetch_count=self.prefetch_count)
        consumer_logger.info(
            "RMQConsumer.consume.set_qos", prefetch_count=self.prefetch_count
        )
        queue = await channel.declare_queue(
            self.queue,
            auto_delete=False,
            durable=self.durable_queue,
            arguments=self.arguments,
        )
        await queue.consume(self.callback)
        consumer_logger.info("RMQConsumer.consume", queue=self.queue)
        try:
            await asyncio.Future()
        finally:
            await connection.close()
