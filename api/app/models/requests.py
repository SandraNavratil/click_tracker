"""Request body models for API endpoints."""

import uuid
from datetime import datetime, timezone

from pydantic import BaseModel, HttpUrl, NaiveDatetime, field_validator

from common.models.click import Click
from common.models.user import User
from common.models.enums import ProcessingStatus


class ClickRequest(BaseModel):
    """Request body for the POST /click endpoint: user, shop URL, and click timestamp."""

    user_id: uuid.UUID
    shop_url: HttpUrl
    timestamp: NaiveDatetime

    @field_validator("timestamp", mode="before")
    @classmethod
    def parse_timestamp(cls, value: int | float | str | datetime) -> NaiveDatetime:
        """Parse timestamp to NaiveDatetime.

        Args:
            value: Timestamp to parse (int, float, str, or datetime).

        Returns:
            NaiveDatetime: Parsed timestamp.

        Raises:
            ValueError: When value is None or not a supported timestamp format.
        """
        if value is None:
            raise ValueError("Timestamp is required")
        if isinstance(value, datetime):
            return value.replace(tzinfo=None)
        if isinstance(value, (int, float)):
            return datetime.fromtimestamp(value, tz=timezone.utc).replace(tzinfo=None)
        if isinstance(value, str):
            return datetime.fromisoformat(value.replace("Z", "+00:00")).replace(
                tzinfo=None
            )
        raise ValueError(
            "Timestamp must be a datetime string, or a number (unix timestamp)"
        )

    def to_click(self) -> Click:
        """Build a Click domain entity from this request.

        Returns:
            Click: Click with generated id, user_id, shop_url, and click_timestamp.
        """
        return Click(
            id=uuid.uuid4(),
            user_id=self.user_id,
            shop_url=str(self.shop_url),
            click_timestamp=self.timestamp,
        )

    def to_user(self) -> User:
        """Build a User domain entity from this request (for first-time user creation).

        Returns:
            User: User with request user_id and processing_state set to new.
        """
        return User(
            id=self.user_id,
            processing_state=ProcessingStatus.new,
        )
