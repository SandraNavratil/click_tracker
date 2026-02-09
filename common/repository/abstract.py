"""Abstract repository for clicks and users (unit of work, get/save)."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Self, Any
from uuid import UUID
from structlog import BoundLogger

from common.models.click import Click, ClickWithUser
from common.models.user import User
from common.models.enums import ProcessingStatus


class AbstractClickRepository(ABC):
    """Abstract repository for persisting and loading User and Click entities."""

    def __init__(self, logger: BoundLogger) -> None:
        """Store the logger for use by implementations.

        Args:
            logger: Structlog bound logger for repository operations.
        """
        self._logger = logger

    @asynccontextmanager
    def unit_of_work(self) -> AsyncIterator[Self]:
        """Create a unit of work; group multiple operations in one transaction.

        Must be used as async context manager. Committed on exit, rolled back on exception.

        Returns:
            Self: Unit of work.

        Raises:
            NotImplementedError: When called on the abstract base (use a concrete implementation).
        """
        # This method would ideally be abstract, but there are issues with asynccontextmanager and abstractmethod.
        # See: https://stackoverflow.com/questions/54204990/python-abstractmethod-with-asynccontextmanager
        raise NotImplementedError

    @abstractmethod
    async def get_user(self, user_id: UUID) -> User:
        """Get a user by id.

        Args:
            user_id: User id.

        Returns:
            User: User entity.

        Raises:
            MissingRequiredAttribute: When not called within a unit of work.
            EntityNotFound: When no user exists for the given user_id.
        """

    @abstractmethod
    async def save_user(self, user: User) -> User:
        """Save a user.

        Args:
            user: User to save.

        Returns:
            User: Saved user.

        Raises:
            MissingRequiredAttribute: When not called within a unit of work.
        """

    @abstractmethod
    async def save_click(self, click: Click) -> Click:
        """Save a click.

        Args:
            click: Click to save.

        Returns:
            Click: Saved click.

        Raises:
            MissingRequiredAttribute: When not called within a unit of work.
        """

    @abstractmethod
    async def get_clicks_with_user_by_user_id(
        self, user_id: UUID
    ) -> list[ClickWithUser]:
        """Get all clicks for a user with user data.

        Args:
            user_id: User id.

        Returns:
            list[ClickWithUser]: List of clicks with user; empty if none.

        Raises:
            MissingRequiredAttribute: When not called within a unit of work.
            EntityNotFound: When no user exists for the given user_id.
        """

    @abstractmethod
    async def get_users_by_processing_state(
        self, processing_state: ProcessingStatus, limit: int = 10000
    ) -> list[User]:
        """Get users with the given processing_state.

        Args:
            processing_state: Processing state to filter by.
            limit: Maximum number of users to return, default is 10000.

        Returns:
            list[User]: List of users with the given processing_state.

        Raises:
            MissingRequiredAttribute: When not called within a unit of work.
        """

    @abstractmethod
    async def update_user_processing_state(
        self, user_id: UUID, processing_state: ProcessingStatus
    ) -> User:
        """Update the processing state of user.

        Args:
            user_id: User id.
            processing_state: Processing state to update user to.

        Returns:
            User: Updated user.

        Raises:
            MissingRequiredAttribute: When not called within a unit of work.
            EntityNotFound: When no user exists for the given user_id.
        """

    @abstractmethod
    async def update_user_values(self, user_id: UUID, values: dict[str, Any]) -> User:
        """Update the values of a user.

        Args:
            user_id: User id.
            values: Values to update user to.

        Returns:
            User: Updated user.

        Raises:
            MissingRequiredAttribute: When not called within a unit of work.
            EntityNotFound: When no user exists for the given user_id.
        """
