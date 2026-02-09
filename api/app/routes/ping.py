"""Health check and ping API routes."""

from http import HTTPStatus

from fastapi import APIRouter

from api.app.models.responses import Ping

router = APIRouter(tags=["Ping"])


@router.get(
    "/ping",
    summary="Health check",
    response_model=Ping,
    responses={
        HTTPStatus.OK: {"description": "Health check OK; returns pong."},
        HTTPStatus.INTERNAL_SERVER_ERROR: {"description": "Internal server error."},
    },
)
async def ping() -> Ping:
    """Health check endpoint; returns a simple pong response.

    Returns:
        Ping: Response with field response set to "pong".
    """
    return Ping(response="pong")
