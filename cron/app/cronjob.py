"""Cron job implementation."""

from common.message_queue.abstract import AbstractQueuePublisher
from common.models.enums import ProcessingStatus
from common.models.queue import QueueMessage, QueueName
from common.repository.abstract import AbstractClickRepository
from common.models.user import User
from cron.app import logger


async def run_cronjob(
    repository: AbstractClickRepository,
    rmq_publisher: AbstractQueuePublisher,
) -> None:
    """Run the cronjob.

    Args:
        repository: Repository to get new users and update user processing state.
        rmq_publisher: Publisher to publish users to RMQ.
    """
    logger.debug("cron.started")
    new_users: list[User] = []
    async with repository.unit_of_work():
        new_users = await repository.get_users_by_processing_state(ProcessingStatus.new)
    logger.info("cron.new_users", number_of_new_users=len(new_users))

    for user in new_users:
        await rmq_publisher.publish(
            message=QueueMessage(user_id=user.id),
            queue=QueueName.CLICK_TRACKER,
        )
        async with repository.unit_of_work():
            await repository.update_user_processing_state(
                user.id, ProcessingStatus.queued
            )

    logger.info("cron.finished")
