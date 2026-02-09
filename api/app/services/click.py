"""Click tracking business logic and persistence."""

from uuid import UUID

from common.models.click import Click, ClickWithUser
from common.models.errors import EntityNotFound
from common.repository.abstract import AbstractClickRepository

from api.app import logger
from api.app.models.requests import ClickRequest


class ClickService:
    """Service for recording user clicks and ensuring user records exist."""

    def __init__(self, click_repository: AbstractClickRepository) -> None:
        """Initialize the click service with a click repository.

        Args:
            click_repository: Repository used to persist clicks and users.
        """
        self.click_repository = click_repository

    async def track_click(
        self,
        click_request: ClickRequest,
    ) -> Click:
        """Track a click.

        Ensures the user exists (creates with status new if not), then persists the click.

        Args:
            click_request: Validated click request from the API.

        Returns:
            Click: The persisted click entity with id.
        """
        logger.info(
            "track_click.start",
            user_id=str(click_request.user_id),
            shop_url=str(click_request.shop_url),
            timestamp=click_request.timestamp.isoformat(),
        )
        async with self.click_repository.unit_of_work():
            try:
                await self.click_repository.get_user(click_request.user_id)
            except EntityNotFound:
                logger.info(
                    "track_click.user_created", user_id=str(click_request.user_id)
                )
                await self.click_repository.save_user(click_request.to_user())

            click = await self.click_repository.save_click(click_request.to_click())
        logger.info(
            "track_click.saved",
            click_id=str(click.id),
            user_id=str(click.user_id),
        )
        return click

    async def get_clicks_with_user_by_user_id(
        self, user_id: UUID
    ) -> list[ClickWithUser]:
        """Get all clicks for a user.

        Args:
            user_id: User id.

        Returns:
            list[ClickWithUser]: List of clicks with nested user; empty if none.

        Raises:
            EntityNotFound: When no user exists for the given user_id.
        """
        async with self.click_repository.unit_of_work():
            return await self.click_repository.get_clicks_with_user_by_user_id(user_id)
