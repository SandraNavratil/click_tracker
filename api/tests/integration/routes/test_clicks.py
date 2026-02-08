"""Integration tests for POST /click using the SQL click repository."""

import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy import select

from common.models.factories import ClickFactory
from dbmodels.src.models import Click as DBClick


@pytest.mark.asyncio
class TestClicks:
    """Integration tests for the /click endpoint with SQL persistence."""

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "payload,description",
        [
            (
                {"shop_url": "https://example.com", "timestamp": "2024-01-01T12:00:00"},
                "missing user_id",
            ),
            (
                {
                    "user_id": "550e8400-e29b-41d4-a716-446655440000",
                    "timestamp": "2024-01-01T12:00:00",
                },
                "missing shop_url",
            ),
            (
                {
                    "user_id": "550e8400-e29b-41d4-a716-446655440000",
                    "shop_url": "https://example.com",
                },
                "missing timestamp",
            ),
        ],
        ids=["missing_user_id", "missing_shop_url", "missing_timestamp"],
    )
    async def test_invalid_request_missing_required_field(
        self, async_test_client: AsyncClient, payload, description
    ):
        """POST /click returns 422 when a required field is missing from the body."""
        response = await async_test_client.post("/click", json=payload)
        assert response.status_code == 422, description

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "payload,description",
        [
            (
                {
                    "user_id": "not-a-uuid",
                    "shop_url": "https://example.com",
                    "timestamp": "2024-01-01T12:00:00",
                },
                "user_id not a valid UUID",
            ),
            (
                {
                    "user_id": 12345,
                    "shop_url": "https://example.com",
                    "timestamp": "2024-01-01T12:00:00",
                },
                "user_id not a string",
            ),
            (
                {
                    "user_id": "550e8400-e29b-41d4-a716-446655440000",
                    "shop_url": "not-a-url",
                    "timestamp": "2024-01-01T12:00:00",
                },
                "shop_url not a valid URL",
            ),
            (
                {
                    "user_id": "550e8400-e29b-41d4-a716-446655440000",
                    "shop_url": "",
                    "timestamp": "2024-01-01T12:00:00",
                },
                "shop_url empty string",
            ),
            (
                {
                    "user_id": "550e8400-e29b-41d4-a716-446655440000",
                    "shop_url": "https://example.com",
                    "timestamp": "not-a-datetime",
                },
                "timestamp invalid string",
            ),
            (
                {
                    "user_id": "550e8400-e29b-41d4-a716-446655440000",
                    "shop_url": "https://example.com",
                    "timestamp": [],
                },
                "timestamp array invalid",
            ),
            (
                {
                    "user_id": "550e8400-e29b-41d4-a716-446655440000",
                    "shop_url": "https://example.com",
                    "timestamp": None,
                },
                "timestamp null invalid",
            ),
        ],
        ids=[
            "user_id_invalid_string",
            "user_id_not_string",
            "shop_url_invalid",
            "shop_url_empty",
            "timestamp_invalid_string",
            "timestamp_array",
            "timestamp_null",
        ],
    )
    async def test_invalid_request_invalid_field_types(
        self, async_test_client: AsyncClient, payload, description
    ):
        """POST /click returns 422 when field types are invalid."""
        response = await async_test_client.post("/click", json=payload)
        assert response.status_code == 422, description

    @pytest.mark.asyncio
    async def test_success_one(self, async_test_client: AsyncClient, click_repository):
        """POST /click with valid payload returns 201 and persists click in SQL."""
        click = ClickFactory.build()
        response = await async_test_client.post(
            "/click",
            json={
                "user_id": str(click.user_id),
                "shop_url": click.shop_url,
                "timestamp": click.click_timestamp.isoformat(),
            },
        )
        assert response.status_code == 201
        response_json = response.json()
        assert "id" in response_json
        click_id_str = response_json["id"]
        assert click_id_str

        async with click_repository.connection.get_session() as session:
            result = await session.execute(
                select(DBClick).where(DBClick.id == uuid.UUID(click_id_str))
            )
            db_click = result.scalar_one_or_none()
        assert db_click is not None
        assert str(db_click.user_id) == str(click.user_id)
        assert db_click.shop_url == click.shop_url

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "timestamp_value",
        [
            "2024-06-15T14:30:00",
            "2024-06-15T14:30:00Z",
            1718458200,
            1718458200.0,
        ],
        ids=["iso_datetime", "iso_datetime_z", "unix_int", "unix_float"],
    )
    async def test_success_timestamp_formats(
        self, async_test_client: AsyncClient, click_repository, timestamp_value
    ):
        """POST /click accepts timestamp as ISO string, ISO with Z, or unix int/float."""
        click = ClickFactory.build()
        payload = {
            "user_id": str(click.user_id),
            "shop_url": click.shop_url,
            "timestamp": timestamp_value,
        }
        response = await async_test_client.post("/click", json=payload)
        assert response.status_code == 201
        assert response.json()["id"]

    @pytest.mark.asyncio
    @pytest.mark.parametrize("num_of_clicks", [2, 5])
    async def test_success_multiple(
        self, async_test_client: AsyncClient, click_repository, num_of_clicks: int
    ):
        """POST /click can record multiple clicks and returns distinct ids."""
        clicks = ClickFactory.batch(size=num_of_clicks)
        ids = set()
        for click in clicks:
            response = await async_test_client.post(
                "/click",
                json={
                    "user_id": str(click.user_id),
                    "shop_url": click.shop_url,
                    "timestamp": click.click_timestamp.isoformat(),
                },
            )
            assert response.status_code == 201
            ids.add(response.json()["id"])
        assert len(ids) == num_of_clicks

    @pytest.mark.asyncio
    async def test_same_user_multiple_clicks(
        self, async_test_client: AsyncClient, click_repository
    ):
        """Same user can post multiple clicks; each receives a unique id."""
        click1 = ClickFactory.build()
        click2 = ClickFactory.build(user_id=click1.user_id, shop_url=click1.shop_url)
        response1 = await async_test_client.post(
            "/click",
            json={
                "user_id": str(click1.user_id),
                "shop_url": click1.shop_url,
                "timestamp": click1.click_timestamp.isoformat(),
            },
        )
        assert response1.status_code == 201
        response2 = await async_test_client.post(
            "/click",
            json={
                "user_id": str(click2.user_id),
                "shop_url": click2.shop_url,
                "timestamp": click2.click_timestamp.isoformat(),
            },
        )
        assert response2.status_code == 201
        assert response1.json()["id"] != response2.json()["id"]
