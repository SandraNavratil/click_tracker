"""In-memory queue publisher and consumer."""

from collections import defaultdict
from collections.abc import Callable, Mapping
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
        """Remove all messages from all in-memory queues (e.g. for test teardown)."""
        self.queues.clear()

    async def publish(
        self,
        message: QueueMessage,
        queue: QueueName,
        *,
        headers: Mapping[str, str | int] | None = None,
    ) -> None:
        """Publish a message to the queue.

        Args:
            message: Message to publish.
            queue: Queue to publish to.
            headers: Optional headers to add to the message.
        """
        self.queues[queue].append(deepcopy(message))


class InMemoryQueueConsumer(AbstractQueueConsumer):
    """In-memory queue consumer."""

    def __init__(self, callback: Callable, queue_name: QueueName) -> None:
        """Initialize the in-memory queue consumer.

        Args:
            callback: Called when a message is received.
            queue_name: Queue name.
        """
        super().__init__(callback, queue_name)

    async def consume(self) -> None:
        """Consume messages from the queue."""
        return None
