"""Pytest fixtures for consumer tests."""

from collections.abc import Generator
import pytest
from common.adapters.enhancer.in_memory import InMemoryEnhancer


@pytest.fixture
def enhancer_adapter() -> Generator[InMemoryEnhancer]:
    """In-memory enhancer adapter."""
    adapter = InMemoryEnhancer()
    yield adapter
