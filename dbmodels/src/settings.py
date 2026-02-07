from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy import AsyncAdaptedQueuePool, Pool


class DatabaseSettings(BaseSettings):
    """Database connection and pool configuration, loaded from environment."""

    model_config = SettingsConfigDict(
        frozen=True,
        validate_default=True,
        env_file="../local.env",
        env_file_encoding="utf-8",
    )
    app_name: str = "click_tracker-dbmodels"
    db_url: str = "postgresql+asyncpg://user:password@0.0.0.0:5432/click_tracker"

    pool_class: type[Pool] = AsyncAdaptedQueuePool
    pool_size: int = 5
    pool_timeout: int = 30  # in seconds
    pool_use_lifo: bool = False
    pool_pre_ping: bool = False
    pool_recycle: int = 1200  # in seconds
    max_overflow: int = 10
    autocommit: bool = False
    autoflush: bool = True
    expire_on_commit: bool = False


settings = DatabaseSettings()
