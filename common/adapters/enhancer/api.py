"""API-based enhancer."""

from typing import override
from uuid import UUID

from common.adapters.enhancer.abstract import AbstractEnhancer, UserProfile


class ApiEnhancer(AbstractEnhancer):
    """Enhancer that calls an external user-profile API. Not implemented; use InMemoryEnhancer instead."""

    @override
    async def get_user_profile(self, user_id: UUID) -> UserProfile:
        """Get user profile by user_id.

        Args:
            user_id: User id.

        Returns:
            UserProfile: username and email_address.
        """
        raise NotImplementedError(
            "ApiEnhancer is not implemented; use InMemoryEnhancer or implement API client."
        )
