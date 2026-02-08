"""Dependency factories for API services."""

from fastapi import Depends

from common.repository.abstract import AbstractClickRepository
from api.app.resource_factories import get_click_repository
from api.app.services.click import ClickService


def get_click_service(
    click_repository: AbstractClickRepository = Depends(get_click_repository),
) -> ClickService:
    """Create and return a ClickService with the injected click repository.

    Args:
        click_repository: Injected by FastAPI from get_click_repository.

    Returns:
        ClickService: Configured click tracking service.
    """
    return ClickService(click_repository=click_repository)
