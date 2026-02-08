"""Queue models."""

from enum import StrEnum
from uuid import UUID

from pydantic import BaseModel


class QueueMessage(BaseModel):
    """Queue message."""

    user_id: UUID


class QueueName(StrEnum):
    """Queue names."""

    CLICK_TRACKER = "click-tracker"
