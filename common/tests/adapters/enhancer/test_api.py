"""Tests for ApiEnhancer."""

import pytest
from uuid import uuid4

from common.adapters.enhancer.api import ApiEnhancer


@pytest.mark.asyncio
async def test_get_user_profile_raises_not_implemented(
    api_enhancer: ApiEnhancer,
) -> None:
    """get_user_profile returns the hardcoded profile."""
    with pytest.raises(NotImplementedError):
        await api_enhancer.get_user_profile(uuid4())
