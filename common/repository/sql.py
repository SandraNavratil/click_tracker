"""SQL implementation of AbstractClickRepository using SQLAlchemy async sessions."""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from typing import Self, override, Any
from uuid import UUID

from sqlalchemy import select, text, update
from sqlalchemy.ext.asyncio import AsyncSession
from structlog import BoundLogger

from common.models.click import Click, ClickWithUser
from common.models.user import User
from common.models.errors import EntityNotFound, MissingRequiredAttribute
from common.repository.abstract import AbstractClickRepository
from dbmodels.src.database import DatabaseConnection
from dbmodels.src.models import Click as DBClick
from dbmodels.src.models import User as DBUser
from common.models.enums import ProcessingStatus


class SQLClickRepository(AbstractClickRepository):
    """Repository that persists users and clicks via SQLAlchemy to the configured database."""

    def __init__(self, logger: BoundLogger, connection: DatabaseConnection) -> None:
        """Initialize with a logger and a database connection.

        Args:
            logger: Structlog bound logger for repository operations.
            connection: Database connection used to obtain async sessions.
        """
        self.connection = connection
        self._current_transaction: AsyncSession | None = None
        super().__init__(logger)

    async def ping(self) -> None:
        """Run a simple query to verify the database is reachable."""
        async with self.connection.get_session() as session:
            await session.execute(text("SELECT 1"))

    @asynccontextmanager
    @override
    async def unit_of_work(self) -> AsyncIterator[Self]:
        """Provide an async session as a unit of work; nested units are not supported.

        Returns:
            Self: Unit of work.

        Raises:
            RuntimeError: When called while already inside a unit of work.
        """
        if self._current_transaction:
            raise RuntimeError("Nested unit of work is not supported")
        try:
            async with self.connection.get_session() as session:
                self._current_transaction = session
                yield self
        finally:
            self._current_transaction = None

    @override
    async def get_user(self, user_id: UUID) -> User:
        """Get user from DB.

        Args:
            user_id: User id.

        Returns:
            User: User.

        Raises:
            MissingRequiredAttribute: When not called within a unit of work.
            EntityNotFound: When no user exists for the given user_id.
        """
        if not self._current_transaction:
            raise MissingRequiredAttribute("Session is required to get user")
        result = await self._current_transaction.execute(
            select(DBUser).where(DBUser.id == user_id)
        )
        db_user = result.scalar_one_or_none()
        if db_user is None:
            raise EntityNotFound("User", str(user_id))
        return User.model_validate(db_user)

    @override
    async def save_user(self, user: User) -> User:
        """Save user to DB.

        Args:
            user: User to save.

        Returns:
            User: Saved user.

        Raises:
            MissingRequiredAttribute: When not called within a unit of work.
        """
        if not self._current_transaction:
            raise MissingRequiredAttribute("Session is required to save user")
        db_user = self._create_db_user(user)
        self._current_transaction.add(db_user)
        return User.model_validate(db_user)

    @override
    async def save_click(self, click: Click) -> Click:
        """Save new click to DB.

        Args:
            click: Click to save.

        Returns:
            Click: Saved click as stored in the DB.

        Raises:
            MissingRequiredAttribute: When not called within a unit of work.
        """
        if not self._current_transaction:
            raise MissingRequiredAttribute("Session is required to save click")
        db_click = self._create_db_click(click)
        self._current_transaction.add(db_click)
        return Click.model_validate(db_click)

    @override
    async def get_clicks_with_user_by_user_id(
        self, user_id: UUID
    ) -> list[ClickWithUser]:
        """Get all clicks for a user with user data from DB.

        Args:
            user_id: User id.

        Returns:
            list[ClickWithUser]: List of clicks with user; empty if user has no clicks.

        Raises:
            MissingRequiredAttribute: When not called within a unit of work.
            EntityNotFound: When no user exists for the given user_id.
        """
        if not self._current_transaction:
            raise MissingRequiredAttribute(
                "Session is required to get clicks by user id"
            )
        result = await self._current_transaction.execute(
            select(DBUser).where(DBUser.id == user_id)
        )
        db_user = result.scalar_one_or_none()
        if db_user is None:
            raise EntityNotFound("User", str(user_id))
        user = User.model_validate(db_user)

        result = await self._current_transaction.execute(
            select(DBClick)
            .where(DBClick.user_id == user_id)
            .order_by(DBClick.click_timestamp.asc())
        )
        db_clicks = result.scalars().all()
        if not db_clicks:
            return []
        return [
            ClickWithUser(
                **Click.model_validate(db_click).model_dump(),
                user=user,
            )
            for db_click in db_clicks
        ]

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

        Raises:
            MissingRequiredAttribute: When not called within a unit of work.
        """
        if not self._current_transaction:
            raise MissingRequiredAttribute(
                "Session is required to get users by processing state"
            )
        result = await self._current_transaction.execute(
            select(DBUser)
            .where(DBUser.processing_state == processing_state)
            .order_by(DBUser.created.asc())
            .limit(limit)
        )
        db_users = result.scalars().all()
        return [User.model_validate(db_user) for db_user in db_users]

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

        Raises:
            MissingRequiredAttribute: When not called within a unit of work.
            EntityNotFound: When no user exists for the given user_id.
        """
        if not self._current_transaction:
            raise MissingRequiredAttribute(
                "Session is required to update users processing state"
            )
        update_statement = (
            update(DBUser)
            .where(DBUser.id == user_id)
            .values(processing_state=processing_state)
            .returning(DBUser)
        )
        result = await self._current_transaction.execute(update_statement)
        db_user = result.scalar_one_or_none()
        if db_user is None:
            raise EntityNotFound("User", str(user_id))
        return User.model_validate(db_user)

    @override
    async def update_user_values(self, user_id: UUID, values: dict[str, Any]) -> User:
        """Update the values of a user.

        Args:
            user_id: User id.
            values: Attributes to update (e.g. username, email_address, processing_state).

        Returns:
            User: Updated user as stored in the database.

        Raises:
            MissingRequiredAttribute: When not called within a unit of work.
            EntityNotFound: When no user exists for the given user_id.
        """
        if not self._current_transaction:
            raise MissingRequiredAttribute("Session is required to update user values")
        update_statement = (
            update(DBUser).where(DBUser.id == user_id).values(values).returning(DBUser)
        )
        result = await self._current_transaction.execute(update_statement)
        db_user = result.scalar_one_or_none()
        if db_user is None:
            raise EntityNotFound("User", str(user_id))
        return User.model_validate(db_user)

    @staticmethod
    def _create_db_click(click: Click) -> DBClick:
        """Create a DBClick from a Click.

        Args:
            click: Click to create DBClick from.

        Returns:
            DBClick: Created DBClick.
        """
        return DBClick(
            id=click.id,
            user_id=click.user_id,
            shop_url=click.shop_url,
            click_timestamp=click.click_timestamp,
        )

    @staticmethod
    def _create_db_user(user: User) -> DBUser:
        """Create a DBUser from a User.

        Args:
            user: User to create DBUser from.

        Returns:
            DBUser: Created DBUser.
        """
        return DBUser(
            id=user.id,
            username=user.username,
            email_address=user.email_address,
            processing_state=user.processing_state,
        )
