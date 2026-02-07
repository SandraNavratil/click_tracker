"""Async SQLAlchemy engine and session management."""

import json
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any
import datetime
import structlog
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from dbmodels.src.settings import DatabaseSettings

logger = structlog.get_logger()


class DatabaseConnection:
    """Manages async SQLAlchemy engine and session factory for the application."""

    def __init__(self, settings: DatabaseSettings, debug: bool):
        """Initialize the database connection with the given settings.

        Args:
            settings: Database configuration (URL, pool options, etc.).
            debug: If True, SQLAlchemy will echo SQL statements to the log.
        """
        self.db_engine = self._create_engine(settings, debug)
        logger.debug("database.create_engine.success")

        self.session_maker: async_sessionmaker[AsyncSession] = async_sessionmaker(
            self.db_engine,
            expire_on_commit=settings.expire_on_commit,
            autocommit=settings.autocommit,
            autoflush=settings.autoflush,
        )
        logger.debug("database.create_sessionmaker.success")

    @asynccontextmanager
    async def get_session(self) -> AsyncGenerator[AsyncSession, None]:
        """Provide an async context manager that yields a single database session.

        Yields:
            AsyncSession: A scoped async session. Session is closed when exiting the context.
        """
        async with self.session_maker() as session:
            logger.debug("get_session.session.begin")
            yield session
        logger.debug("get_session.session.end")

    @staticmethod
    def _create_engine(settings: DatabaseSettings, debug: bool) -> AsyncEngine:
        """Build the async SQLAlchemy engine from settings.

        Args:
            settings: Database configuration.
            debug: Whether to echo SQL (for debugging).

        Returns:
            AsyncEngine: The configured async engine.
        """
        pool_parameters: dict[str, Any] = {
            "poolclass": settings.pool_class,
        }
        if settings.pool_class != pool.NullPool:
            pool_parameters.update(
                {
                    "pool_size": settings.pool_size,
                    "pool_timeout": settings.pool_timeout,
                    "pool_pre_ping": settings.pool_pre_ping,
                    "pool_use_lifo": settings.pool_use_lifo,
                    "max_overflow": settings.max_overflow,
                    "pool_recycle": settings.pool_recycle,
                }
            )

        return create_async_engine(
            settings.db_url,
            echo=debug,
            json_serializer=lambda x: json.dumps(x, cls=JSONEncoder),
            **pool_parameters,
        )


class JSONEncoder(json.JSONEncoder):
    """JSON encoder that serializes datetime objects to ISO format strings."""

    def default(self, o: Any) -> Any:
        """Encode non-standard types for JSON serialization.

        Args:
            o: The object to encode.

        Returns:
            ISO format string for datetime; otherwise delegates to the parent encoder.
        """
        if isinstance(o, datetime.datetime):
            return o.isoformat()
        return super().default(o)
