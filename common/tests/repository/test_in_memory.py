"""Tests for InMemoryClickRepository (unit of work, get/save user and click)."""

import pytest

from common.models.enums import ProcessingStatus
from common.models.errors import EntityNotFound, MissingRequiredAttribute
from common.models.factories import ClickFactory, UserFactory
from common.repository.in_memory import InMemoryClickRepository


@pytest.mark.asyncio
class TestInMemoryClickRepository:
    """Tests for InMemoryClickRepository using in-process storage and unit of work."""

    async def test_unit_of_work_rollback_on_exception(
        self,
        in_memory_click_repository: InMemoryClickRepository,
    ) -> None:
        """Uncommitted changes are discarded when unit_of_work exits with an exception."""
        repository = in_memory_click_repository
        user = UserFactory.build()
        with pytest.raises(ValueError):
            async with repository.unit_of_work():
                await repository.save_user(user)
                raise ValueError("abort")
        with pytest.raises(EntityNotFound):
            async with repository.unit_of_work():
                await repository.get_user(user.id)

    @pytest.mark.parametrize("user_count", [0, 1, 2])
    async def test_save_user_success(
        self,
        in_memory_click_repository: InMemoryClickRepository,
        user_count: int,
    ) -> None:
        """Saving users within unit_of_work stores the expected number in storage."""
        repository = in_memory_click_repository
        users = [UserFactory.build() for _ in range(user_count)]
        async with repository.unit_of_work():
            for user in users:
                await repository.save_user(user)
        user_keys = [k for k in repository._storage if k.startswith("user_")]
        assert len(user_keys) == user_count

    async def test_save_user_missing_transaction(
        self,
        in_memory_click_repository: InMemoryClickRepository,
    ) -> None:
        """save_user without an active unit_of_work raises MissingRequiredAttribute."""
        repository = in_memory_click_repository
        user = UserFactory.build()
        with pytest.raises(MissingRequiredAttribute):
            await repository.save_user(user)

    @pytest.mark.parametrize("click_count", [0, 1, 2])
    async def test_save_click_success(
        self,
        in_memory_click_repository: InMemoryClickRepository,
        click_count: int,
    ) -> None:
        """Saving clicks within unit_of_work stores the expected number in storage."""
        repository = in_memory_click_repository
        user = UserFactory.build()
        async with repository.unit_of_work():
            await repository.save_user(user)
        clicks = [ClickFactory.build(user_id=user.id) for _ in range(click_count)]
        async with repository.unit_of_work():
            for click in clicks:
                await repository.save_click(click)
        click_keys = [k for k in repository._storage if k.startswith("click_")]
        assert len(click_keys) == click_count

    async def test_save_click_missing_transaction(
        self,
        in_memory_click_repository: InMemoryClickRepository,
    ) -> None:
        """save_click without an active unit_of_work raises MissingRequiredAttribute."""
        repository = in_memory_click_repository
        click = ClickFactory.build()
        with pytest.raises(MissingRequiredAttribute):
            await repository.save_click(click)

    @pytest.mark.parametrize("num_users", [1, 2, 5])
    async def test_get_user(
        self,
        in_memory_click_repository: InMemoryClickRepository,
        num_users: int,
    ) -> None:
        """get_user within unit_of_work returns the same user that was saved."""
        repository = in_memory_click_repository
        users = [UserFactory.build() for _ in range(num_users)]
        async with repository.unit_of_work():
            for user in users:
                await repository.save_user(user)
        for expected_user in users:
            async with repository.unit_of_work():
                returned_user = await repository.get_user(expected_user.id)
            assert returned_user == expected_user

    async def test_get_user_not_found(
        self,
        in_memory_click_repository: InMemoryClickRepository,
    ) -> None:
        """get_user for a non-existent id raises EntityNotFound."""
        repository = in_memory_click_repository
        for _ in range(3):
            user = UserFactory.build()
            async with repository.unit_of_work():
                await repository.save_user(user)
        with pytest.raises(EntityNotFound):
            async with repository.unit_of_work():
                await repository.get_user(UserFactory.build().id)

    async def test_get_user_missing_transaction(
        self,
        in_memory_click_repository: InMemoryClickRepository,
    ) -> None:
        """get_user without unit_of_work raises MissingRequiredAttribute."""
        repository = in_memory_click_repository
        user = UserFactory.build()
        async with repository.unit_of_work():
            await repository.save_user(user)
        user_id = user.id
        with pytest.raises(MissingRequiredAttribute):
            await repository.get_user(user_id)

    async def test_get_users_by_processing_state_returns_only_matching(
        self,
        in_memory_click_repository: InMemoryClickRepository,
    ) -> None:
        """get_users_by_processing_state returns only users with the given state."""
        repository = in_memory_click_repository
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
        self,
        in_memory_click_repository: InMemoryClickRepository,
    ) -> None:
        """get_users_by_processing_state returns at most `limit` users."""
        repository = in_memory_click_repository
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
        self,
        in_memory_click_repository: InMemoryClickRepository,
    ) -> None:
        """get_users_by_processing_state returns empty list when no users have that state."""
        repository = in_memory_click_repository
        user_queued = UserFactory.build(processing_state=ProcessingStatus.queued)
        async with repository.unit_of_work():
            await repository.save_user(user_queued)
        async with repository.unit_of_work():
            result = await repository.get_users_by_processing_state(
                ProcessingStatus.new
            )
        assert result == []

    async def test_get_users_by_processing_state_missing_transaction(
        self,
        in_memory_click_repository: InMemoryClickRepository,
    ) -> None:
        """get_users_by_processing_state without unit_of_work raises MissingRequiredAttribute."""
        repository = in_memory_click_repository
        user = UserFactory.build()
        async with repository.unit_of_work():
            await repository.save_user(user)
        with pytest.raises(MissingRequiredAttribute):
            await repository.get_users_by_processing_state(ProcessingStatus.new)

    async def test_update_user_processing_state_success(
        self,
        in_memory_click_repository: InMemoryClickRepository,
    ) -> None:
        """update_user_processing_state updates state and persists after commit."""
        repository = in_memory_click_repository
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
        self,
        in_memory_click_repository: InMemoryClickRepository,
    ) -> None:
        """update_user_processing_state for non-existent user raises EntityNotFound."""
        repository = in_memory_click_repository
        user = UserFactory.build()
        with pytest.raises(EntityNotFound):
            async with repository.unit_of_work():
                await repository.update_user_processing_state(
                    user.id, ProcessingStatus.queued
                )

    async def test_update_user_processing_state_missing_transaction(
        self,
        in_memory_click_repository: InMemoryClickRepository,
    ) -> None:
        """update_user_processing_state without unit_of_work raises MissingRequiredAttribute."""
        repository = in_memory_click_repository
        user = UserFactory.build()
        async with repository.unit_of_work():
            await repository.save_user(user)
        user_id = user.id
        with pytest.raises(MissingRequiredAttribute):
            await repository.update_user_processing_state(
                user_id, ProcessingStatus.queued
            )
