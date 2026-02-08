"""Settings loaded from environment and optional env file."""

import os

from pydantic import AmqpDsn, TypeAdapter
from pydantic_settings import BaseSettings, SettingsConfigDict

from common.models.enums import EnvironmentEnum


class SettingsWithConfig(BaseSettings):
    """Base for settings that load from ../local.env with env vars taking precedence."""

    model_config = SettingsConfigDict(
        # envvars have precedence over envfile
        env_file="../local.env",
        env_file_encoding="utf-8",
        frozen=True,
    )


class AppSettings(SettingsWithConfig):
    """Application-wide settings: app name, version, and environment-derived flags."""

    app_name: str = "click-tracker-common"
    package_version: str = "latest"
    environment: EnvironmentEnum = EnvironmentEnum.local

    @property
    def local_environment(self) -> bool:
        """True if environment is local."""
        return self.environment == EnvironmentEnum.local

    @property
    def debug(self) -> bool:
        """True if not production (enables debug logging and tools)."""
        return self.environment != EnvironmentEnum.production

    @property
    def is_production(self) -> bool:
        """True if environment is production."""
        return self.environment == EnvironmentEnum.production

    @property
    def user_agent(self) -> str:
        """User-Agent string for outbound requests."""
        return f"{self.app_name}/{self.package_version} ({self.environment})"


class RabbitMQSettings(SettingsWithConfig):
    """RabbitMQ connection and exchange settings."""

    rabbit_host: str = "localhost"
    rabbit_password: str = "guest"
    rabbit_username: str = "guest"
    rabbit_vhost: str = ""
    rabbit_query_params: str = "heartbeat=600&blocked_connection_timeout=300"
    rabbit_exchange_name: str = "click-tracker-exchange"
    rabbit_exchange_type: str = "direct"
    rabbit_queue_type: str = "quorum"
    rabbit_delivery_limit: int = 3
    max_retry_count: int = 3
    rabbit_concurrency: int = 1

    @property
    def rabbit_url(self) -> str:
        """AMQP URL: from RMQ_URL env var if set, otherwise built from host/user/password/vhost."""
        if url := os.getenv("RMQ_URL"):
            return url
        return str(
            TypeAdapter(AmqpDsn).validate_python(
                f"amqp://{self.rabbit_username}:{self.rabbit_password}@{self.rabbit_host}:5672/{self.rabbit_vhost}?{self.rabbit_query_params}"
            )
        )

    @property
    def rabbit_dead_letter_exchange_name(self) -> str:
        """Name of the dead-letter exchange for this app."""
        return f"{self.rabbit_exchange_name}-dlx"


app_settings = AppSettings()
rabbit_settings = RabbitMQSettings()
