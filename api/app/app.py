"""FastAPI application instance, router registration, and global exception handlers."""

import json
import logging
from http import HTTPStatus

from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError
from starlette.requests import Request
from starlette.responses import RedirectResponse

from api.app import logger
from api.app.create_api import create_app
from api.app.log_config import EndpointFilter
from api.app.routes.docs import router as docs_router
from api.app.routes.ping import router as ping_router
from api.app.routes.click import router as click_router
from common.models.errors import EntityNotFound, UnexpectedParameterValue
from common.settings import app_settings

app = create_app()
app.include_router(docs_router)
app.include_router(ping_router)
app.include_router(click_router)


@app.exception_handler(SQLAlchemyError)
async def sqlalchemy_error_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    """Handle SQLAlchemyError exceptions."""
    logger.exception("sqlalchemy_error", detail=str(exc))
    detail = str(exc) if app_settings.debug else "An unexpected error occurred"
    return JSONResponse(
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        content={"detail": detail},
    )


@app.exception_handler(Exception)
async def general_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """Handle any unhandled exceptions."""
    logger.exception("unhandled_error", detail=str(exc))
    return JSONResponse(
        status_code=HTTPStatus.INTERNAL_SERVER_ERROR,
        content={"detail": "An unexpected error occurred"},
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(
    _: Request, exc: RequestValidationError
) -> JSONResponse:
    """Handle validation errors and format them to human-readable JSONResponse."""
    logger.exception("validation_error", detail=exc.errors(), body=exc.body)
    content = {"detail": json.loads(json.dumps(exc.errors(), default=str))}
    if app_settings.debug and exc.body is not None:
        content["body"] = exc.body
    return JSONResponse(status_code=422, content=content)


@app.exception_handler(EntityNotFound)
async def entity_not_found_handler(_: Request, exc: EntityNotFound) -> JSONResponse:
    """Return 404 when a requested entity does not exist."""
    return JSONResponse(
        status_code=HTTPStatus.NOT_FOUND,
        content={"detail": str(exc)},
    )


@app.exception_handler(UnexpectedParameterValue)
async def unexpected_parameter_exception_handler(
    _: Request, exc: UnexpectedParameterValue
) -> JSONResponse:
    """Handle exceptions caused by unexpected parameter values during request processing."""
    logger.warning("unexpected_parameter", detail=str(exc))
    return JSONResponse(
        status_code=HTTPStatus.BAD_REQUEST,
        content={"detail": str(exc)},
    )


@app.get("/", include_in_schema=False)
async def redirect_to_ui() -> RedirectResponse:
    """Redirects to the UI."""
    return RedirectResponse(url="/ui", status_code=HTTPStatus.PERMANENT_REDIRECT)


logging.getLogger("uvicorn.access").addFilter(EndpointFilter("/ping"))
