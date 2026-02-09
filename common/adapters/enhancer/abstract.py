"""Abstract enhancer."""

from abc import ABC, abstractmethod
from uuid import UUID

from common.models.adapters.enhancer import UserProfile


class AbstractEnhancer(ABC):
    """Abstract enhancer class."""

    @abstractmethod
    async def get_user_profile(self, user_id: UUID) -> UserProfile:
        """Get user profile by user_id.

        Args:
            user_id: User id.

        Returns:
            UserProfile: username and email_address.
        """
