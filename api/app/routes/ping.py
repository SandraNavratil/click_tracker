"""Health check and ping API routes."""

from fastapi import APIRouter

from api.app.models.responses import Ping

router = APIRouter(tags=["Ping"])


@router.get("/ping", summary="Health check", response_model=Ping)
async def ping() -> Ping:
    """Health check endpoint; returns a simple pong response.

    Returns:
        Ping: Response with field response set to "pong".
    """
    return Ping(response="pong")
