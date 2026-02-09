"""Click tracking API routes."""

from uuid import UUID

from fastapi import APIRouter, Depends
from http import HTTPStatus

from api.app.models.requests import ClickRequest
from api.app.models.responses import RequestAccepted, ClickWithUserResponse
from api.app.services.click import ClickService
from api.app.services.service_factories import get_click_service

router = APIRouter(tags=["Click"])


@router.get(
    "/users/{user_id}/clicks",
    summary="Get all clicks for a user.",
    status_code=HTTPStatus.OK,
    response_model=list[ClickWithUserResponse],
    responses={
        HTTPStatus.OK: {"description": "List of clicks for the user (possibly empty)."},
        HTTPStatus.NOT_FOUND: {"description": "No user with the given user_id exists."},
        HTTPStatus.UNPROCESSABLE_ENTITY: {
            "description": "Validation error (e.g. invalid user_id format)."
        },
        HTTPStatus.INTERNAL_SERVER_ERROR: {"description": "Internal server error."},
    },
)
async def get_clicks_by_user_id(
    user_id: UUID, click_service: ClickService = Depends(get_click_service)
) -> list[ClickWithUserResponse]:
    """Return all clicks for the given user_id, ordered by click_timestamp.

    Args:
        user_id: User id (path parameter).
        click_service: Injected click tracking service.

    Returns:
        list[ClickWithUserResponse]: List of clicks with user fields; empty if none.
    """
    clicks_with_user = await click_service.get_clicks_with_user_by_user_id(user_id)
    return [
        ClickWithUserResponse(
            id=str(click.id),
            user_id=str(click.user_id),
            shop_url=click.shop_url,
            click_timestamp=click.click_timestamp.isoformat(),
            username=click.user.username,
            email_address=click.user.email_address,
        )
        for click in clicks_with_user
    ]


@router.post(
    "/click",
    summary="Track a click by a user.",
    status_code=HTTPStatus.CREATED,
    response_model=RequestAccepted,
    responses={
        HTTPStatus.CREATED: {
            "description": "Click recorded; returns the created click id."
        },
        HTTPStatus.BAD_REQUEST: {
            "description": "Bad request (e.g. unexpected parameter)."
        },
        HTTPStatus.UNPROCESSABLE_ENTITY: {
            "description": "Validation error (invalid body)."
        },
        HTTPStatus.INTERNAL_SERVER_ERROR: {"description": "Internal server error."},
    },
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
