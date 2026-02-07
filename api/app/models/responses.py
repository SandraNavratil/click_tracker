"""Response models for API endpoints."""

from pydantic import BaseModel


class RequestAccepted(BaseModel):
    """Response body for POST /click: id of the created click record."""

    id: str


class Ping(BaseModel):
    """Response body for GET /ping health check."""

    response: str
