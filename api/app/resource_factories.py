"""Dependency factories for repository and database resources."""

from api.app import logger
from common.repository.abstract import AbstractClickRepository
from common.repository.sql import SQLClickRepository
from common.settings import app_settings
from dbmodels.src.database import DatabaseConnection
from dbmodels.src.settings import settings as db_settings

_db_connection = DatabaseConnection(db_settings, debug=app_settings.debug)


async def get_click_repository() -> AbstractClickRepository:
    """Create and return a click repository backed by the shared database connection.

    Returns:
        AbstractClickRepository: SQL click repository instance.
    """
    return SQLClickRepository(logger, _db_connection)
