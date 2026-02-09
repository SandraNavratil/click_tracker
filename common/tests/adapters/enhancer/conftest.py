"""Pytest fixtures for adapter tests."""

import pytest

from common.adapters.enhancer.in_memory import InMemoryEnhancer
from common.adapters.enhancer.api import ApiEnhancer


@pytest.fixture
def in_memory_enhancer() -> InMemoryEnhancer:
    """Return a fresh in-memory enhancer for each test."""
    return InMemoryEnhancer()


@pytest.fixture
def api_enhancer() -> ApiEnhancer:
    """Return a fresh API enhancer for each test."""
    return ApiEnhancer()
