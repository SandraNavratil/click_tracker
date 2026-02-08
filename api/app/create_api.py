"""Factory for creating and configuring the FastAPI application."""

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from api.app.log_config import LoggingMiddleware
from common.settings import app_settings


def create_app() -> FastAPI:
    """Create and configure the Click Tracker FastAPI application.

    Sets up title, description, static files, and logging middleware.
    Swagger/ReDoc are disabled here; custom docs routes are registered in app.py.

    Returns:
        FastAPI: Configured FastAPI application instance.
    """

    description = """<div>API for the Click Tracker system. It receives click events from clients and records them.</div>
        <div>Source code can be found <a href="https://github.com/SandraNavratil/click_tracker">here</a>.</div>
        """
    app = FastAPI(
        title="Click Tracker API",
        debug=app_settings.debug,
        description=description,
        version="1.0.0",
        contact={
            "name": "Sandra Navrátil",
            "email": "sandra.i.navratil@gmail.com",
        },
        docs_url=None,  # Disable default Swagger UI route, we have custom one
        redoc_url=None,  # Disable default Redoc route, we have custom one
    )

    static_path = "api/app/static"
    app.mount("/static", StaticFiles(directory=static_path), name="static")
    app.add_middleware(LoggingMiddleware)

    return app
