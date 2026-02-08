"""Abstract classes for message queue."""

from abc import ABC, abstractmethod
from collections.abc import Callable

from common.models.queue import QueueMessage, QueueName


class AbstractQueuePublisher(ABC):
    """Abstract class for message queue publishers."""

    @abstractmethod
    async def publish(self, message: QueueMessage, queue: QueueName) -> None:
        """Publish a message to the queue."""

    @abstractmethod
    async def ping(self) -> None:
        """Ping the queue publisher."""


class AbstractQueueConsumer(ABC):
    """Abstract class for message queue consumers."""

    def __init__(self, callback: Callable, queue_name: QueueName) -> None:
        """Initialize the queue consumer.

        Args:
            callback: Function to be called when a message is received.
            queue_name: Name of the queue to consume from.
        """
        self.callback = callback
        self.queue = queue_name

    @abstractmethod
    async def consume(self) -> None:
        """Consume messages from the queue."""
