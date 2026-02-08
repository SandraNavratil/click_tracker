"""Domain model for a user and their processing state."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict

from common.models.enums import ProcessingStatus


class User(BaseModel):
    """Domain entity: user id, optional profile fields, and processing_state."""

    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        validate_default=True,
        use_enum_values=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

    id: UUID
    username: str | None = None
    email_address: str | None = None
    processing_state: ProcessingStatus = ProcessingStatus.new
