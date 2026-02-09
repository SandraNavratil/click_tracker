"""Tests for SQLClickRepository (async unit of work, get/save user and click)."""

import pytest
import structlog
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.sql import func

from common.models.enums import ProcessingStatus
from common.models.errors import EntityNotFound, MissingRequiredAttribute
from common.models.factories import ClickFactory, UserFactory
from common.repository.sql import SQLClickRepository
from dbmodels.src.database import DatabaseConnection
from dbmodels.src.models import Click as DBClick
from dbmodels.src.models import User as DBUser

logger = structlog.get_logger()


@pytest.mark.usefixtures("clear_db")
@pytest.mark.asyncio
class TestSQLClickRepository:
    """Tests for SQLClickRepository using async sessions and unit of work."""

    async def test_ping(self, db_connection: DatabaseConnection) -> None:
        """Ping runs a simple query and does not raise."""
        repository = SQLClickRepository(logger, db_connection)
        await repository.ping()

    async def test_nested_unit_of_work(self, db_connection: DatabaseConnection) -> None:
        """Nested unit_of_work raises RuntimeError."""
        repository = SQLClickRepository(logger, db_connection)
        with pytest.raises(RuntimeError):
            async with repository.unit_of_work():
                async with repository.unit_of_work():
                    pass

    @pytest.mark.parametrize("user_count", [0, 1, 2])
    async def test_save_user_success(
        self, db_connection: DatabaseConnection, user_count: int
    ) -> None:
        """Saving users within unit_of_work persists the expected number of rows."""
        repository = SQLClickRepository(logger, db_connection)
        users = [UserFactory.build() for _ in range(user_count)]
        async with repository.unit_of_work():
            for user in users:
                await repository.save_user(user)
        async with db_connection.get_session() as session:
            result = await session.execute(select(func.count()).select_from(DBUser))
            row_count = result.scalar_one()
        assert row_count == user_count

    @pytest.mark.parametrize("user_count", [1, 2])
    async def test_save_user_duplicate(
        self, db_connection: DatabaseConnection, user_count: int
    ) -> None:
        """Saving the same user again raises IntegrityError."""
        repository = SQLClickRepository(logger, db_connection)
        users = [UserFactory.build() for _ in range(user_count)]
        async with repository.unit_of_work():
            for user in users:
                await repository.save_user(user)
        with pytest.raises(IntegrityError):
            async with repository.unit_of_work():
                await repository.save_user(users[0])

    async def test_save_user_missing_transaction(
        self, db_connection: DatabaseConnection
    ) -> None:
        """save_user without an active unit_of_work raises MissingRequiredAttribute."""
        repository = SQLClickRepository(logger, db_connection)
        user = UserFactory.build()
        with pytest.raises(MissingRequiredAttribute):
            await repository.save_user(user)

    @pytest.mark.parametrize("click_count", [0, 1, 2])
    async def test_save_click_success(
        self, db_connection: DatabaseConnection, click_count: int
    ) -> None:
        """Saving clicks within unit_of_work persists the expected number of rows."""
        repository = SQLClickRepository(logger, db_connection)
        user = UserFactory.build()
        async with repository.unit_of_work():
            await repository.save_user(user)
        clicks = [ClickFactory.build(user_id=user.id) for _ in range(click_count)]
        async with repository.unit_of_work():
            for click in clicks:
                await repository.save_click(click)
        async with db_connection.get_session() as session:
            result = await session.execute(select(func.count()).select_from(DBClick))
            row_count = result.scalar_one()
        assert row_count == click_count

    @pytest.mark.parametrize("click_count", [1, 2])
    async def test_save_click_duplicate(
        self, db_connection: DatabaseConnection, click_count: int
    ) -> None:
        """Saving the same click again raises IntegrityError."""
        repository = SQLClickRepository(logger, db_connection)
        user = UserFactory.build()
        async with repository.unit_of_work():
            await repository.save_user(user)
        clicks = [ClickFactory.build(user_id=user.id) for _ in range(click_count)]
        async with repository.unit_of_work():
            for click in clicks:
                await repository.save_click(click)
        with pytest.raises(IntegrityError):
            async with repository.unit_of_work():
                await repository.save_click(clicks[0])

    async def test_save_click_missing_transaction(
        self, db_connection: DatabaseConnection
    ) -> None:
        """save_click without an active unit_of_work raises MissingRequiredAttribute."""
        repository = SQLClickRepository(logger, db_connection)
        user = UserFactory.build()
        async with repository.unit_of_work():
            await repository.save_user(user)
        click = ClickFactory.build(user_id=user.id)
        with pytest.raises(MissingRequiredAttribute):
            await repository.save_click(click)

    @pytest.mark.parametrize("num_users", [1, 2, 5])
    async def test_get_user(
        self,
        db_connection: DatabaseConnection,
        num_users: int,
    ) -> None:
        """get_user within unit_of_work returns the same user that was saved."""
        repository = SQLClickRepository(logger, db_connection)
        users = [UserFactory.build() for _ in range(num_users)]
        async with repository.unit_of_work():
            for user in users:
                await repository.save_user(user)
        for expected_user in users:
            async with repository.unit_of_work():
                returned_user = await repository.get_user(expected_user.id)
            assert returned_user == expected_user

    async def test_get_user_not_found(self, db_connection: DatabaseConnection) -> None:
        """get_user for a non-existent id raises EntityNotFound."""
        repository = SQLClickRepository(logger, db_connection)
        for _ in range(3):
            user = UserFactory.build()
            async with repository.unit_of_work():
                await repository.save_user(user)
        with pytest.raises(EntityNotFound):
            async with repository.unit_of_work():
                await repository.get_user(UserFactory.build().id)

    async def test_get_user_missing_transaction(
        self, db_connection: DatabaseConnection
    ) -> None:
        """get_user without an active unit_of_work raises MissingRequiredAttribute."""
        repository = SQLClickRepository(logger, db_connection)
        user_id = UserFactory.build().id
        with pytest.raises(MissingRequiredAttribute):
            await repository.get_user(user_id)

    async def test_get_users_by_processing_state_returns_only_matching(
        self, db_connection: DatabaseConnection
    ) -> None:
        """get_users_by_processing_state returns only users with the given state."""
        repository = SQLClickRepository(logger, db_connection)
        user_new = UserFactory.build(processing_state=ProcessingStatus.new)
        user_queued = UserFactory.build(processing_state=ProcessingStatus.queued)
        user_done = UserFactory.build(processing_state=ProcessingStatus.done)
        async with repository.unit_of_work():
            await repository.save_user(user_new)
            await repository.save_user(user_queued)
            await repository.save_user(user_done)
        async with repository.unit_of_work():
            result_new = await repository.get_users_by_processing_state(
                ProcessingStatus.new
            )
            result_queued = await repository.get_users_by_processing_state(
                ProcessingStatus.queued
            )
            result_done = await repository.get_users_by_processing_state(
                ProcessingStatus.done
            )
        assert len(result_new) == 1 and result_new[0].id == user_new.id
        assert len(result_queued) == 1 and result_queued[0].id == user_queued.id
        assert len(result_done) == 1 and result_done[0].id == user_done.id

    async def test_get_users_by_processing_state_respects_limit(
        self, db_connection: DatabaseConnection
    ) -> None:
        """get_users_by_processing_state returns at most `limit` users."""
        repository = SQLClickRepository(logger, db_connection)
        users = [
            UserFactory.build(processing_state=ProcessingStatus.new) for _ in range(5)
        ]
        async with repository.unit_of_work():
            for user in users:
                await repository.save_user(user)
        async with repository.unit_of_work():
            result = await repository.get_users_by_processing_state(
                ProcessingStatus.new, limit=2
            )
            result_all = await repository.get_users_by_processing_state(
                ProcessingStatus.new, limit=10
            )
        assert len(result) == 2
        assert len(result_all) == 5

    async def test_get_users_by_processing_state_empty_when_no_match(
        self, db_connection: DatabaseConnection
    ) -> None:
        """get_users_by_processing_state returns empty list when no users have that state."""
        repository = SQLClickRepository(logger, db_connection)
        user_queued = UserFactory.build(processing_state=ProcessingStatus.queued)
        async with repository.unit_of_work():
            await repository.save_user(user_queued)
        async with repository.unit_of_work():
            result = await repository.get_users_by_processing_state(
                ProcessingStatus.new
            )
        assert result == []

    async def test_get_users_by_processing_state_missing_transaction(
        self, db_connection: DatabaseConnection
    ) -> None:
        """get_users_by_processing_state without unit_of_work raises MissingRequiredAttribute."""
        repository = SQLClickRepository(logger, db_connection)
        with pytest.raises(MissingRequiredAttribute):
            await repository.get_users_by_processing_state(ProcessingStatus.new)

    async def test_update_user_processing_state_success(
        self, db_connection: DatabaseConnection
    ) -> None:
        """update_user_processing_state updates state and persists after commit."""
        repository = SQLClickRepository(logger, db_connection)
        user = UserFactory.build(processing_state=ProcessingStatus.new)
        async with repository.unit_of_work():
            await repository.save_user(user)
        async with repository.unit_of_work():
            updated = await repository.update_user_processing_state(
                user.id, ProcessingStatus.done
            )
        assert updated.processing_state == ProcessingStatus.done
        async with repository.unit_of_work():
            loaded = await repository.get_user(user.id)
        assert loaded.processing_state == ProcessingStatus.done

    async def test_update_user_processing_state_not_found(
        self, db_connection: DatabaseConnection
    ) -> None:
        """update_user_processing_state for non-existent user raises EntityNotFound."""
        repository = SQLClickRepository(logger, db_connection)
        user = UserFactory.build()
        with pytest.raises(EntityNotFound):
            async with repository.unit_of_work():
                await repository.update_user_processing_state(
                    user.id, ProcessingStatus.queued
                )

    async def test_update_user_processing_state_missing_transaction(
        self, db_connection: DatabaseConnection
    ) -> None:
        """update_user_processing_state without unit_of_work raises MissingRequiredAttribute."""
        repository = SQLClickRepository(logger, db_connection)
        user = UserFactory.build()
        async with repository.unit_of_work():
            await repository.save_user(user)
        user_id = user.id
        with pytest.raises(MissingRequiredAttribute):
            await repository.update_user_processing_state(
                user_id, ProcessingStatus.queued
            )

    async def test_update_user_values_success(
        self, db_connection: DatabaseConnection
    ) -> None:
        """update_user_values updates fields and persists after commit."""
        repository = SQLClickRepository(logger, db_connection)
        user = UserFactory.build(
            username="old_name",
            email_address="old@example.com",
            processing_state=ProcessingStatus.new,
        )
        async with repository.unit_of_work():
            await repository.save_user(user)
        new_username = "new_name"
        new_email = "new@example.com"
        async with repository.unit_of_work():
            updated = await repository.update_user_values(
                user.id,
                {
                    "username": new_username,
                    "email_address": new_email,
                    "processing_state": ProcessingStatus.done,
                },
            )
        assert updated.username == new_username
        assert updated.email_address == new_email
        assert updated.processing_state == ProcessingStatus.done
        async with repository.unit_of_work():
            loaded = await repository.get_user(user.id)
        assert loaded.username == new_username
        assert loaded.email_address == new_email
        assert loaded.processing_state == ProcessingStatus.done

    async def test_update_user_values_not_found(
        self, db_connection: DatabaseConnection
    ) -> None:
        """update_user_values for non-existent user raises EntityNotFound."""
        repository = SQLClickRepository(logger, db_connection)
        user = UserFactory.build()
        with pytest.raises(EntityNotFound):
            async with repository.unit_of_work():
                await repository.update_user_values(user.id, {"username": "updated"})

    async def test_update_user_values_missing_transaction(
        self, db_connection: DatabaseConnection
    ) -> None:
        """update_user_values without unit_of_work raises MissingRequiredAttribute."""
        repository = SQLClickRepository(logger, db_connection)
        user = UserFactory.build()
        async with repository.unit_of_work():
            await repository.save_user(user)
        user_id = user.id
        with pytest.raises(MissingRequiredAttribute):
            await repository.update_user_values(user_id, {"username": "updated"})
