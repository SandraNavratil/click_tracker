"""Enhancer adapter model."""

from pydantic import BaseModel, ConfigDict


class UserProfile(BaseModel):
    """Result of enhancing a user: username and email_address."""

    model_config = ConfigDict(frozen=True)

    username: str
    email_address: str
