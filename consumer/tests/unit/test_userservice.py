"""Unit tests for Consumer."""

import pytest
from uuid import uuid4

from common.adapters.enhancer.in_memory import InMemoryEnhancer
from common.models.enums import ProcessingStatus
from common.models.queue import QueueMessage, QueueName
from common.models.user import User
from common.repository.abstract import AbstractClickRepository
from consumer.app.services.userservice import UserService
from common.models.errors import EntityNotFound


class TestUserService:
    """Test UserService."""

    @pytest.mark.asyncio
    async def test_process_message_success(
        self,
        click_repository: AbstractClickRepository,
        rmq_publisher,
        enhancer_adapter: InMemoryEnhancer,
        collect_messages,
    ) -> None:
        """Tests that the UserService processes a message successfully."""
        user_id = uuid4()
        user = User(
            id=user_id,
            username=None,
            email_address=None,
            processing_state=ProcessingStatus.queued,
        )

        async with click_repository.unit_of_work():
            await click_repository.save_user(user)

        message = QueueMessage(user_id=user_id)
        await rmq_publisher.publish(message, QueueName.CLICK_TRACKER)

        messages = collect_messages()
        assert len(messages) == 1
        consumed = messages[0]

        user_service = UserService(
            click_repository=click_repository,
            enhancer_adapter=enhancer_adapter,
        )
        await user_service.process_message(consumed)

        async with click_repository.unit_of_work():
            updated = await click_repository.get_user(user_id)

        assert updated.processing_state == ProcessingStatus.done
        assert updated.username == "test"
        assert updated.email_address == "test@test.com"

    @pytest.mark.asyncio
    async def test_process_message_user_not_found(
        self,
        click_repository: AbstractClickRepository,
        rmq_publisher,
        enhancer_adapter: InMemoryEnhancer,
        collect_messages,
    ) -> None:
        """Tests that the UserService raises an error when the user does not exist in the database."""

        user_id = uuid4()
        message = QueueMessage(user_id=user_id)
        await rmq_publisher.publish(message, QueueName.CLICK_TRACKER)

        messages = collect_messages()
        assert len(messages) == 1
        consumed = messages[0]

        user_service = UserService(
            click_repository=click_repository,
            enhancer_adapter=enhancer_adapter,
        )

        with pytest.raises(EntityNotFound):
            await user_service.process_message(consumed)

        async with click_repository.unit_of_work():
            with pytest.raises(EntityNotFound):
                await click_repository.get_user(user_id)
