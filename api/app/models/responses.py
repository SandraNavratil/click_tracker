"""Response models for API endpoints."""

from pydantic import BaseModel


class ClickWithUserResponse(BaseModel):
    """Click with user data in GET /users/{user_id}/clicks response."""

    id: str
    user_id: str
    shop_url: str
    click_timestamp: str
    username: str | None = None
    email_address: str | None = None


class RequestAccepted(BaseModel):
    """Response body for POST /click: id of the created click record."""

    id: str


class Ping(BaseModel):
    """Response body for GET /ping health check."""

    response: str
