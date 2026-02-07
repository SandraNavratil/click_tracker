"""Logging configuration: request-scoped context middleware and endpoint filters for uvicorn access logs."""

import logging
from collections.abc import Awaitable, Callable
import uuid

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from structlog.contextvars import bind_contextvars, clear_contextvars


class EndpointFilter(logging.Filter):
    """Filter for logging to only include requests to the given URL."""

    def __init__(self, url_to_filter: str, logger_name: str = ""):
        """Initialize the filter.

        Args:
            url_to_filter: URL to filter.
            logger_name: Name of the logger.
        """
        super().__init__(name=logger_name)
        self.url_to_filter = url_to_filter

    def filter(self, record: logging.LogRecord) -> bool:
        """Filter the record to only include requests to the given URL.

        Args:
            record: Record to filter.

        Returns:
            bool: True if the record should be logged, False otherwise.
        """
        return record.getMessage().find(self.url_to_filter) == -1


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for logging requests to the given URL."""

    async def dispatch(
        self, request: Request, call_next: Callable[[Request], Awaitable[Response]]
    ) -> Response:
        """Prepare all the context variables in logger.

        Args:
            request: Request received by app.
            call_next: Function (endpoint) that was called.

        Returns:
            Response: Response of the endpoint itself.
        """
        clear_contextvars()
        bind_contextvars(
            request_id=str(uuid.uuid4()),
            url=request.url.path,
            method=request.method,
            user_agent=request.headers.get("User-Agent"),
        )

        response = await call_next(request)

        return response
