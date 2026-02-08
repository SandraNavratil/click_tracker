"""Click tracking API routes."""

from fastapi import APIRouter, Depends
from http import HTTPStatus

from api.app.models.requests import ClickRequest
from api.app.models.responses import RequestAccepted
from api.app.services.click import ClickService
from api.app.services.service_factories import get_click_service

router = APIRouter(tags=["Click"])


@router.post(
    "/click",
    summary="Track a click by a user.",
    status_code=HTTPStatus.CREATED,
    response_model=RequestAccepted,
)
async def click(
    request: ClickRequest, click_service: ClickService = Depends(get_click_service)
) -> RequestAccepted:
    """Record a user click (user_id, shop_url, timestamp) and return the created click id.

    Args:
        request: Validated body with user_id, shop_url, and timestamp.
        click_service: Injected click tracking service.

    Returns:
        RequestAccepted: Response containing the id of the persisted click.
    """
    click = await click_service.track_click(request)
    response = RequestAccepted(id=str(click.id))
    return response
