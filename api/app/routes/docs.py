"""API documentation routes: Swagger UI and ReDoc."""

from fastapi import APIRouter
from fastapi.openapi.docs import get_redoc_html, get_swagger_ui_html
from fastapi.responses import HTMLResponse

router = APIRouter()


@router.get("/ui", include_in_schema=False)
async def swagger() -> HTMLResponse:
    """Serve Swagger UI HTML for interactive API documentation.

    Returns:
        HTMLResponse: Swagger UI page with OpenAPI spec from /openapi.json.
    """
    return get_swagger_ui_html(
        openapi_url="/openapi.json",
        title="Click Tracker API",
        swagger_favicon_url="/static/favicon.png",
    )


@router.get("/redoc", include_in_schema=False)
async def redoc_handler() -> HTMLResponse:
    """Serve ReDoc HTML for API documentation.

    Returns:
        HTMLResponse: ReDoc page with OpenAPI spec from /openapi.json.
    """
    return get_redoc_html(
        openapi_url="/openapi.json",
        title="Click Tracker API",
        redoc_favicon_url="/static/favicon.png",
    )
