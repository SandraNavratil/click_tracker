import pytest
from uuid import uuid4
from sqlalchemy import select
from sqlalchemy.exc import DatabaseError
from sqlalchemy.ext.asyncio import AsyncSession

from dbmodels.src import models
from dbmodels.tests.factories import ClickFactory, UserFactory

REQUIRED_ARGUMENTS = ["user_id", "shop_url", "click_timestamp"]


class TestClick:
    """Tests for the Click model."""

    @pytest.mark.asyncio
    async def test_save_new_click(self, async_db_session: AsyncSession):
        """Persisting a new click stores it and it can be loaded by id."""
        user = UserFactory()
        async_db_session.add(user)
        await async_db_session.flush()

        click = ClickFactory(user_id=user.id)
        click_id = click.id

        async_db_session.add(click)
        await async_db_session.flush()

        assert click.id is not None

        result = await async_db_session.scalars(
            select(models.Click).where(models.Click.id == click_id)
        )
        fetched_clicks = result.all()
        assert len(fetched_clicks) == 1
        assert fetched_clicks[0].user_id == user.id

    @pytest.mark.asyncio
    async def test_click_loads_user(self, async_db_session: AsyncSession):
        """Click relationship loads the associated user with correct attributes."""
        user = UserFactory(username="testuser")
        async_db_session.add(user)
        await async_db_session.flush()

        click = ClickFactory(user_id=user.id)
        async_db_session.add(click)
        await async_db_session.flush()
        await async_db_session.refresh(click)

        assert click.user is not None
        assert click.user.id == user.id
        assert click.user.username == "testuser"

    @pytest.mark.asyncio
    @pytest.mark.parametrize("required_field", REQUIRED_ARGUMENTS)
    async def test_missing_required_argument(
        self, async_db_session: AsyncSession, required_field: str
    ):
        """Flush raises DatabaseError when a required field is None."""
        user = UserFactory()
        async_db_session.add(user)
        await async_db_session.flush()

        click = ClickFactory(user_id=user.id)
        assert getattr(click, required_field) is not None
        setattr(click, required_field, None)

        async_db_session.add(click)
        with pytest.raises(DatabaseError):
            await async_db_session.flush()

    @pytest.mark.asyncio
    async def test_missing_user(self, async_db_session: AsyncSession):
        """Flush raises DatabaseError when user_id does not reference an existing user."""
        click = ClickFactory(user_id=uuid4())
        async_db_session.add(click)
        with pytest.raises(DatabaseError):
            await async_db_session.flush()
