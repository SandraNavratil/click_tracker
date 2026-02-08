"""Structlog configuration: JSON vs pretty console and optional debug log filtering."""

from typing import Any

import structlog
import structlog_pretty
from structlog.contextvars import merge_contextvars


def configure_structlog(debug: bool, local_format: bool) -> None:
    """Set up structlog with one of two predefined config schemes.

    Args:
        debug: If True, debug-level logs are kept; otherwise dropped.
        local_format: If True, use pretty console output; otherwise JSON.
    """
    base_processors = []
    if not debug:
        base_processors.append(drop_debug_logs)

    processors = [
        *base_processors,
        merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.TimeStamper("iso"),
        structlog_pretty.NumericRounder(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.processors.JSONRenderer(),
    ]

    debug_processors = [
        *base_processors,
        merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog_pretty.NumericRounder(),
        structlog.processors.TimeStamper("iso"),
        structlog.processors.ExceptionPrettyPrinter(),
        structlog.processors.UnicodeDecoder(),
        structlog.dev.ConsoleRenderer(pad_event_to=25),
    ]

    structlog.configure(
        processors=debug_processors if local_format else processors,
        logger_factory=structlog.PrintLoggerFactory(),
        wrapper_class=structlog.stdlib.BoundLogger,
    )


def drop_debug_logs(_: Any, level: str, event_dict: dict[str, Any]) -> dict[str, Any]:
    """Processor that drops the event when level is debug; otherwise returns event_dict."""
    if level == "debug":
        raise structlog.DropEvent
    return event_dict
