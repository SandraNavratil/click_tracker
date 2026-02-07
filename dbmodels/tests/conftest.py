import nest_asyncio
import pytest_asyncio
from sqlalchemy import inspect, text
from sqlalchemy.ext.asyncio import AsyncEngine

from dbmodels.src import models
from dbmodels.src.database import DatabaseConnection
from dbmodels.src.settings import settings

nest_asyncio.apply()


def _get_table_names_sync(conn):
    """Return list of table names for the given sync connection (for use with run_sync)."""
    return inspect(conn).get_table_names()


@pytest_asyncio.fixture(scope="session")
async def engine() -> AsyncEngine:
    """Session-scoped async database engine for tests. Disposed after the session."""
    _conn = DatabaseConnection(settings, debug=True)
    yield _conn.db_engine
    await _conn.db_engine.dispose()


@pytest_asyncio.fixture(scope="session")
async def db_safe_check(engine: AsyncEngine):
    """Ensure the database is empty (or only has alembic_version) before tests run."""
    async with engine.connect() as conn:
        table_names = await conn.run_sync(_get_table_names_sync)
    assert table_names in ([], ["alembic_version"]), "DB not empty!!"


@pytest_asyncio.fixture(scope="session")
async def db_teardown(engine: AsyncEngine, db_safe_check):
    """Drop all tables before and after the test session (clean slate for migrations)."""
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.drop_all)
        await conn.execute(text("DROP TABLE IF EXISTS alembic_version;"))
    yield
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.drop_all)
        await conn.execute(text("DROP TABLE IF EXISTS alembic_version;"))


@pytest_asyncio.fixture(scope="session")
async def db_create(db_safe_check, engine: AsyncEngine, db_teardown):
    """Create all tables from models for the test session."""
    async with engine.begin() as conn:
        await conn.run_sync(models.Base.metadata.create_all)
    return


@pytest_asyncio.fixture(scope="function")
async def async_db_session(db_create):
    """Per-test async session. Each test gets a session; changes are rolled back after the test."""
    async_db_connection = DatabaseConnection(settings, debug=True)
    async with async_db_connection.get_session() as session:
        yield session
        await session.rollback()
