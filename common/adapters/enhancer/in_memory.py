"""In-memory enhancer."""

import asyncio
from typing import override
from uuid import UUID

from common.adapters.enhancer.abstract import AbstractEnhancer, UserProfile

_MIN_INTERVAL = 1 / 200  # 200 req/s


class InMemoryEnhancer(AbstractEnhancer):
    """In-memory enhancer that always returns hardcoded user profile."""

    @override
    async def get_user_profile(self, user_id: UUID) -> UserProfile:
        """Get user profile by user_id.

        Args:
            user_id: User id.

        Returns:
            UserProfile: username and email_address (always hardcoded).
        """
        await asyncio.sleep(_MIN_INTERVAL)
        return UserProfile(username="test", email_address="test@test.com")
