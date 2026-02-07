"""Abstract repository for clicks and users (unit of work, get/save)."""

from abc import ABC, abstractmethod
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Self
from uuid import UUID

from structlog import BoundLogger

from common.models.click import Click
from common.models.user import User


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
        """

    @abstractmethod
    async def save_user(self, user: User) -> User:
        """Save a user to the database.

        Args:
            user: User to save.

        Returns:
            User: Saved user.
        """

    @abstractmethod
    async def save_click(self, click: Click) -> Click:
        """Save a click to the database.

        Args:
            click: Click to save.

        Returns:
            Click: Saved click as stored in the DB.
        """
