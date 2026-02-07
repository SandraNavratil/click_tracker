"""Pytest fixtures for common tests: async DB engine, clear_db, and database connection."""

from collections.abc import AsyncGenerator

import pytest
import pytest_asyncio
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine, create_async_engine

from dbmodels.src import models
from dbmodels.src.database import DatabaseConnection
from dbmodels.src.settings import settings


@pytest_asyncio.fixture(scope="function")
def engine() -> AsyncEngine:
    """Create a function-scoped async SQLAlchemy engine for tests."""
    return create_async_engine(settings.db_url, echo=True)


@pytest_asyncio.fixture
async def clear_db(engine: AsyncEngine) -> AsyncGenerator[None, None]:
    """Reset DB schema before and after each test (drop/create tables)."""
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.drop_all)
        await conn.run_sync(models.Base.metadata.create_all)

    yield

    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.drop_all)
        await conn.execute(text("DROP TABLE IF EXISTS alembic_version;"))


@pytest.fixture
def db_connection() -> DatabaseConnection:
    """Return a DatabaseConnection using test settings with debug enabled."""
    return DatabaseConnection(settings, debug=True)
