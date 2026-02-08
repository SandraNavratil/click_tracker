"""Pytest fixtures for API tests: FastAPI app, async client, and SQL click repository."""

from collections.abc import AsyncGenerator, Generator

import pytest
import pytest_asyncio
import structlog
from httpx import ASGITransport, AsyncClient

from api.app.app import app
from api.app.resource_factories import get_click_repository
from common.repository.sql import SQLClickRepository
from dbmodels.src.database import DatabaseConnection

logger = structlog.get_logger(__name__)
# Import all fixtures from common tests
from common.tests.conftest import *  # noqa


@pytest.fixture(scope="session")
def fastapi_app():
    """Return the FastAPI application instance for the test session."""
    return app


@pytest.fixture(autouse=True)
def _clear_dependency_overrides(fastapi_app) -> Generator[None, None, None]:
    """Clear FastAPI dependency overrides after each test to avoid leakage."""
    yield
    fastapi_app.dependency_overrides.clear()


@pytest_asyncio.fixture(scope="function")
async def async_test_client(fastapi_app) -> AsyncGenerator[AsyncClient, None]:
    """Yield an async HTTP client configured for the FastAPI app (ASGI transport)."""
    async with AsyncClient(
        transport=ASGITransport(app=fastapi_app), base_url="http://test"
    ) as client:
        yield client


@pytest.fixture
def click_repository(
    clear_db, fastapi_app, db_connection: DatabaseConnection
) -> SQLClickRepository:
    """SQL click repository with a clean DB (clear_db runs first when this fixture is used)."""
    repository = SQLClickRepository(logger=logger, connection=db_connection)
    fastapi_app.dependency_overrides[get_click_repository] = lambda: repository
    return repository
