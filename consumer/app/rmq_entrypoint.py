"""RMQ entrypoint: wire-up consumer, repository, enhancer and message handling."""

from aio_pika.abc import AbstractIncomingMessage
from aiormq.abc import AbstractChannel
from structlog.contextvars import bind_contextvars, clear_contextvars

from consumer.app import logger, app_settings
from common.settings import rabbit_settings
from common.message_queue.rmq_queue import RMQPublisher
from common.models.queue import QueueMessage, QueueName
from common.repository.sql import SQLClickRepository
from consumer.app.services.userservice import UserService
from dbmodels.src.database import DatabaseConnection
from dbmodels.src.settings import settings as db_settings
from common.adapters.enhancer.in_memory import InMemoryEnhancer

db_connection = DatabaseConnection(settings=db_settings, debug=app_settings.debug)
enhancer_adapter = InMemoryEnhancer()

rmq_publisher = RMQPublisher(
    url=rabbit_settings.rabbit_url,
    exchange_name=rabbit_settings.rabbit_exchange_name,
    queue_names=[QueueName.CLICK_TRACKER],
)


async def requeue_message(
    message: QueueMessage,
    channel: AbstractChannel,
    delivery_tag: int,
    should_retry: bool = False,
    delay_time_min: int = 5,
    delivery_count: int = 0,
) -> None:
    """Nack (DLQ) or ack and republish the message for retry.

    Args:
        message: The queue message to nack or republish.
        channel: AMQP channel for ack/nack.
        delivery_tag: Delivery tag to ack or nack.
        should_retry: If True, republish message with delay then ack; otherwise nack (send to DLQ).
        delay_time_min: Delay in minutes before message is visible again (used when should_retry).
        delivery_count: Current delivery count; incremented when republishing.
    """
    if not should_retry:
        await channel.basic_nack(delivery_tag=delivery_tag, requeue=False)
        return

    delay_time_ms = delay_time_min * 60 * 1000
    properties = {"x-delay": delay_time_ms, "x-delivery-count": delivery_count + 1}
    await rmq_publisher.publish(message, QueueName.CLICK_TRACKER, headers=properties)
    await channel.basic_ack(delivery_tag=delivery_tag)


def handle_exception(e: Exception, last_try: bool) -> bool:
    """Log the exception and return whether the message should be retried.

    Args:
        e: The exception that was raised.
        last_try: True if max retries have been reached.

    Returns:
        True if the message should be retried, False otherwise.
    """
    if not last_try:
        logger.exception("consumer.temporary_failed", err_class=e.__class__.__name__)
        return True

    logger.exception("consumer.failed", err_class=e.__class__.__name__)
    return False


async def handle_incoming_message(
    message: AbstractIncomingMessage,
) -> None:
    """Parse RMQ message, run UserService logic, ack or requeue on success/failure.

    Deserializes the body as QueueMessage, runs UserService.process_message within a
    unit of work, and acks on success. On exception, logs and optionally requeues
    with delay based on retry count.

    Args:
        message: The RMQ message to handle.
    """
    clear_contextvars()
    logger.info("consumer.init")
    payload = QueueMessage.model_validate_json(message.body)
    bind_contextvars(user_id=payload.user_id)

    message_headers = message.headers or {}
    delivery_count = int(message_headers.get("x-delivery-count", "0"))
    is_last_try = delivery_count >= rabbit_settings.max_retry_count

    click_repository = SQLClickRepository(logger, db_connection)

    try:
        await UserService(
            click_repository=click_repository,
            enhancer_adapter=enhancer_adapter,
        ).process_message(payload)
    except Exception as e:
        should_retry = handle_exception(e, is_last_try)
        await requeue_message(
            payload,
            message.channel,
            message.delivery_tag,
            should_retry=should_retry,
            delivery_count=delivery_count,
        )
        return

    await message.channel.basic_ack(delivery_tag=message.delivery_tag)
    logger.info("consumer.success")
