"""Factories for domain models: User, Click, ClickWithUser."""

from collections.abc import Callable
from typing import Any
from uuid import UUID

import faker
from polyfactory import Use
from polyfactory.decorators import post_generated
from polyfactory.factories.pydantic_factory import ModelFactory
from pydantic import BaseModel, NaiveDatetime

from common.models.click import Click, ClickWithUser
from common.models.enums import ProcessingStatus
from common.models.user import User

fake = faker.Faker()


class CustomModelFactoryWithDatetime[T: BaseModel](ModelFactory[T]):
    """Custom model factory with providers for datetime types.

    https://polyfactory.litestar.dev/usage/handling_custom_types.html#creating-custom-base-factories
    """

    __is_base_factory__ = True
    __check_model__ = True
    fake = faker.Faker()

    @classmethod
    def get_provider_map(cls) -> dict[Any, Callable]:
        """Return type-to-callable map for NaiveDatetime and UUID (plus parent providers)."""
        providers_map = super().get_provider_map()
        return {
            NaiveDatetime: cls.fake.date_time_this_decade,
            UUID: lambda: fake.uuid4(),
            **providers_map,
        }


class UserFactory(CustomModelFactoryWithDatetime[User]):
    """Factory for building User domain instances in tests."""

    __model__ = User

    id = Use(fake.uuid4)
    username = Use(fake.user_name)
    email_address = Use(fake.email)
    processing_state = ProcessingStatus.new


class ClickFactory(CustomModelFactoryWithDatetime[Click]):
    """Factory for building Click domain instances in tests."""

    __model__ = Click

    id = Use(fake.uuid4)
    user_id = Use(fake.uuid4)
    shop_url = Use(fake.url)
    click_timestamp = Use(fake.date_time_this_decade)


class ClickWithUserFactory(CustomModelFactoryWithDatetime[ClickWithUser]):
    """Factory for building ClickWithUser domain instances in tests."""

    __model__ = ClickWithUser

    id = Use(fake.uuid4)
    shop_url = Use(fake.url)
    click_timestamp = Use(fake.date_time_this_decade)
    user = Use(UserFactory.build)

    @post_generated
    @classmethod
    def user_id(cls, user: User) -> UUID:
        """Set user_id from the generated nested user's id."""
        return user.id
