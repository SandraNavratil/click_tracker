"""Consumer application module."""

import structlog
from structlog import BoundLogger

from common.config.log_config import configure_structlog
from common.settings import app_settings

configure_structlog(
    debug=app_settings.debug, local_format=app_settings.local_environment
)

logger: BoundLogger = structlog.get_logger(app_settings.app_name)
