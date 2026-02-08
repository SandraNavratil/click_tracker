"""Tests for Alembic migrations (upgrade/downgrade)."""

import pytest
from alembic import command
from alembic.config import Config

alembic_cfg = Config()
alembic_cfg.set_main_option("script_location", "dbmodels/alembic")


@pytest.mark.asyncio
async def test_upgrade(db_teardown):  # noqa: RUF029 usage of async
    """Alembic upgrade to head runs without error."""
    command.upgrade(alembic_cfg, "head")


@pytest.mark.asyncio
async def test_upgrade_downgrade_upgrade(db_teardown):  # noqa: RUF029 usage of async
    """Upgrade to head, downgrade one revision, then upgrade again succeeds."""
    command.upgrade(alembic_cfg, "head")
    command.downgrade(alembic_cfg, "-1")
    command.upgrade(alembic_cfg, "head")
