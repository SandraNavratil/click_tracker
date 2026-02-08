"""In-memory queue publisher and consumer."""

from collections import defaultdict
from collections.abc import Callable
from copy import deepcopy

from common.message_queue.abstract import AbstractQueueConsumer, AbstractQueuePublisher
from common.models.queue import QueueMessage, QueueName


class InMemoryQueuePublisher(AbstractQueuePublisher):
    """In-memory queue publisher."""

    def __init__(self) -> None:
        """Initialize the in-memory queue publisher."""
        self.queues: dict[QueueName, list[QueueMessage]] = defaultdict(list)

    async def ping(self) -> None:
        """Ping the queue publisher."""
        return None

    def clear(self) -> None:
        """Clear the in-memory queue publisher."""
        self.queues.clear()

    async def publish(self, message: QueueMessage, queue: QueueName) -> None:
        """Publish a message to the queue."""
        self.queues[queue].append(deepcopy(message))


class InMemoryQueueConsumer(AbstractQueueConsumer):
    """In-memory queue consumer."""

    def __init__(self, callback: Callable, queue_name: QueueName) -> None:
        """Initialize the in-memory queue consumer."""
        super().__init__(callback, queue_name)

    async def consume(self) -> None:
        """Consume messages from the queue."""
        return None
