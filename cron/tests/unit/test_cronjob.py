"""Unit tests for cron job."""

import pytest

from common.models.enums import ProcessingStatus
from common.models.queue import QueueMessage, QueueName
from common.models.factories import UserFactory
from cron.app.cronjob import run_cronjob


@pytest.mark.asyncio
class TestCronJob:
    """Tests for cron job."""

    async def test_empty_database(self, click_repository, rmq_publisher):
        """Tests that the cron job does nothing when the database is empty."""
        await run_cronjob(repository=click_repository, rmq_publisher=rmq_publisher)
        assert not rmq_publisher.queues

    async def test_no_new_users_when_all_queued(self, click_repository, rmq_publisher):
        """Tests that the cron job does nothing when all users are queued."""
        user = UserFactory.build(processing_state=ProcessingStatus.queued)
        async with click_repository.unit_of_work():
            await click_repository.save_user(user)
        await run_cronjob(repository=click_repository, rmq_publisher=rmq_publisher)
        assert not rmq_publisher.queues

    @pytest.mark.parametrize("number_of_users", [1, 5])
    async def test_new_users_published_and_marked_queued(
        self, click_repository, rmq_publisher, number_of_users: int
    ):
        """Tests that the cron job publishes new users and marks them as queued."""
        users = UserFactory.batch(
            size=number_of_users, processing_state=ProcessingStatus.new
        )
        async with click_repository.unit_of_work():
            for user in users:
                await click_repository.save_user(user)
        await run_cronjob(repository=click_repository, rmq_publisher=rmq_publisher)
        assert len(rmq_publisher.queues) == 1
        messages = rmq_publisher.queues[QueueName.CLICK_TRACKER]
        assert len(messages) == number_of_users
        published_user_ids = {
            m.user_id for m in messages if isinstance(m, QueueMessage)
        }
        assert published_user_ids == {u.id for u in users}
        for user in users:
            async with click_repository.unit_of_work():
                updated = await click_repository.get_user(user.id)
            assert updated.processing_state == ProcessingStatus.queued
