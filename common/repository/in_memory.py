"""In-memory implementation of AbstractClickRepository for tests and demos."""

from copy import deepcopy
from contextlib import asynccontextmanager
from typing import AsyncIterator, ClassVar, Self, cast, override, Any
from uuid import UUID

from pydantic import BaseModel
from structlog import BoundLogger

from common.models.click import Click
from common.models.user import User
from common.models.errors import EntityNotFound, MissingRequiredAttribute
from common.repository.abstract import AbstractClickRepository
from common.models.enums import ProcessingStatus


class InMemoryClickRepository(AbstractClickRepository):
    """Repository that stores users and clicks in process memory with transaction-like commits."""

    _storage: ClassVar[dict[str, BaseModel]] = {}
    _uncommitted_storage: ClassVar[dict[str, BaseModel]] = {}

    def __init__(self, logger: BoundLogger) -> None:
        """Initialize with a logger; storage is class-level shared state.

        Args:
            logger: Logger for repository operations.
        """
        self.transaction_started: bool = False
        super().__init__(logger)

    @asynccontextmanager
    @override
    async def unit_of_work(self) -> AsyncIterator[Self]:
        """Start a unit of work; commits on exit, rollback on exception.

        Returns:
            Self: Unit of work.
        """
        try:
            self.transaction_started = True
            yield self
        except Exception as e:
            self._rollback()
            raise e
        finally:
            self.transaction_started = False
        self._commit()

    @override
    async def get_user(self, user_id: UUID) -> User:
        """Return the user for the given id (raises EntityNotFound if not found).

        Args:
            user_id: User id.

        Returns:
            User: User.
        """
        if not self.transaction_started:
            raise MissingRequiredAttribute("Session is required to get user.")
        key = self._get_key(str(user_id), "user")
        if key not in self._storage:
            raise EntityNotFound("User", str(user_id))
        return cast(User, self._storage[key])

    @override
    async def save_user(self, user: User) -> User:
        """Store user in uncommitted storage.

        Args:
            user: User to save.

        Returns:
            User: Saved user.
        """
        if not self.transaction_started:
            raise MissingRequiredAttribute("Session is required to save new user.")
        self._uncommitted_storage[self._get_key(str(user.id), "user")] = user
        return user

    @override
    async def save_click(self, click: Click) -> Click:
        """Store click in uncommitted storage.

        Args:
            click: Click to save.

        Returns:
            Click: Saved click.
        """
        if not self.transaction_started:
            raise MissingRequiredAttribute("Session is required to save new click.")
        self._uncommitted_storage[self._get_key(str(click.id), "click")] = click
        return click

    @override
    async def get_users_by_processing_state(
        self, processing_state: ProcessingStatus, limit: int = 10000
    ) -> list[User]:
        """Get users with the given processing_state.

        Args:
            processing_state: Processing state to filter by.
            limit: Maximum number of users to return, default is 10000.

        Returns:
            list[User]: List of users with the given processing_state.
        """
        if not self.transaction_started:
            raise MissingRequiredAttribute(
                "Session is required to get users by processing state."
            )
        return [
            cast(User, value)
            for key, value in self._storage.items()
            if key.startswith("user_")
            and cast(User, value).processing_state == processing_state
        ][:limit]

    @override
    async def update_user_processing_state(
        self, user_id: UUID, processing_state: ProcessingStatus
    ) -> User:
        """Update the processing state of a user.

        Args:
            user_id: User id.
            processing_state: Processing state to update user to.

        Returns:
            User: Updated user.
        """
        if not self.transaction_started:
            raise MissingRequiredAttribute(
                "Session is required to update user processing state."
            )
        key = self._get_key(str(user_id), "user")
        if (user := self._storage.get(key)) is None:
            raise EntityNotFound("User", str(user_id))
        user = cast(User, deepcopy(user))
        user.processing_state = processing_state
        self._uncommitted_storage[key] = user
        return user

    @override
    async def update_user_values(self, user_id: UUID, values: dict[str, Any]) -> User:
        """Update the values of a user.

        Args:
            user_id: User id.
            values: Values to update user to.

        Returns:
            User: Updated user.
        """
        if not self.transaction_started:
            raise MissingRequiredAttribute("Session is required to update user values.")
        key = self._get_key(str(user_id), "user")
        if (user := self._storage.get(key)) is None:
            raise EntityNotFound("User", str(user_id))
        user = cast(User, deepcopy(user))
        for attr_name, value in values.items():
            setattr(user, attr_name, value)
        self._uncommitted_storage[key] = user
        return user

    def _commit(self) -> None:
        """Apply uncommitted changes to storage and clear the uncommitted map."""
        self._storage.update(deepcopy(self._uncommitted_storage))
        self._uncommitted_storage.clear()

    def _rollback(self) -> None:
        """Discard uncommitted changes."""
        self._uncommitted_storage.clear()

    def clear(self) -> None:
        """Remove all stored data (for test teardown)."""
        self._storage.clear()
        self._uncommitted_storage.clear()

    @staticmethod
    def _get_key(_id: str, collection: str = "") -> str:
        """Build a storage key from collection and id, e.g. 'user_<uuid>' or 'click_<uuid>'.

        Args:
            _id: Id to build key from.
            collection: Collection name.

        Returns:
            str: Storage key.
        """
        if collection:
            return f"{collection}_{_id}"
        return _id
