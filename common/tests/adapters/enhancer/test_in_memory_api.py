"""Tests for InMemoryEnhancer."""

import pytest
from uuid import uuid4

from common.adapters.enhancer.in_memory import InMemoryEnhancer


@pytest.mark.asyncio
async def test_get_user_profile_returns_hardcoded_profile(
    in_memory_enhancer: InMemoryEnhancer,
) -> None:
    """get_user_profile returns the hardcoded profile."""
    profile = await in_memory_enhancer.get_user_profile(uuid4())
    assert profile.username == "test"
    assert profile.email_address == "test@test.com"
