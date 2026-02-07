"""Tests for the User SQLAlchemy model (persistence and processing_state)."""

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from dbmodels.src import models
from dbmodels.tests.factories import UserFactory


class TestUser:
    """Tests for the User model."""

    @pytest.mark.asyncio
    async def test_save_new_user(self, async_db_session: AsyncSession):
        """Persisting a new user stores it with default processing_state and can be loaded by id."""
        user = UserFactory()
        user_id = user.id

        async_db_session.add(user)
        await async_db_session.flush()

        assert user.id is not None

        result = await async_db_session.scalars(
            select(models.User).where(models.User.id == user_id)
        )
        fetched_users = result.all()
        assert len(fetched_users) == 1
        assert fetched_users[0].processing_state == models.Status.new

    @pytest.mark.asyncio
    @pytest.mark.parametrize("processing_state", list(models.Status))
    async def test_save_user_with_processing_state(
        self, async_db_session: AsyncSession, processing_state: models.Status
    ):
        """User can be saved with any Status and the value is persisted correctly."""
        user = UserFactory(processing_state=processing_state)
        user_id = user.id

        async_db_session.add(user)
        await async_db_session.flush()

        result = await async_db_session.scalars(
            select(models.User).where(models.User.id == user_id)
        )
        fetched = result.one()
        assert fetched.processing_state == processing_state
