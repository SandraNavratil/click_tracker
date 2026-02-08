"""Domain models for click and click-with-user entities."""

from uuid import UUID

from pydantic import BaseModel, ConfigDict, NaiveDatetime

from common.models.user import User


class Click(BaseModel):
    """Domain entity: a single click (id, user_id, shop_url, click_timestamp)."""

    model_config = ConfigDict(
        from_attributes=True,
        validate_assignment=True,
        validate_default=True,
        use_enum_values=True,
        populate_by_name=True,
        arbitrary_types_allowed=True,
    )

    id: UUID
    user_id: UUID
    shop_url: str
    click_timestamp: NaiveDatetime


class ClickWithUser(Click):
    """Click with nested user, e.g. when loaded with a repository relationship."""

    user: User
