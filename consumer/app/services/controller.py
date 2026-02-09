"""Controller."""

from structlog.contextvars import bind_contextvars

from common.models.queue import QueueMessage
from common.repository.abstract import AbstractClickRepository
from common.adapters.enhancer.abstract import AbstractEnhancer
from common.models.enums import ProcessingStatus
from consumer.app import logger


class Controller:
    """Controller service."""

    def __init__(
        self,
        click_repository: AbstractClickRepository,
        enhancer_adapter: AbstractEnhancer,
    ) -> None:
        """Initialize the controller with repository and enhancer dependencies.

        Args:
            click_repository: Repository for users and clicks.
            enhancer_adapter: Adapter to fetch user profile (e.g. username, email) by user_id.
        """
        self.click_repository = click_repository
        self.enhancer_adapter = enhancer_adapter

    async def handle_message(self, message: QueueMessage) -> None:
        """Handle a message from the queue: enrich user and persist in one transaction.

        Fetches user profile from the enhancer, then updates the user's username,
        email_address and processing_state to done within a single unit of work.

        Args:
            message: Queue message containing at least user_id to process.

        Raises:
            NotImplementedError: When the enhancer adapter is not implemented.
            EntityNotFound: When the user does not exist in the repository.
            MissingRequiredAttribute: When repository operations are used outside a unit of work.
            RuntimeError: When the repository does not support nested units of work.
        """
        bind_contextvars(user_id=message.user_id)
        logger.info("handle_message.init")

        user_profile = await self.enhancer_adapter.get_user_profile(message.user_id)
        logger.info("handle_message.get_user_profile.success")

        async with self.click_repository.unit_of_work():
            await self.click_repository.update_user_values(
                message.user_id,
                {
                    "username": user_profile.username,
                    "email_address": user_profile.email_address,
                    "processing_state": ProcessingStatus.done,
                },
            )

        logger.info("handle_message.finish")
