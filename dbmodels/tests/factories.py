from collections.abc import Callable
from unittest.mock import MagicMock
from uuid import uuid4

from factory import lazy_attribute
from factory.alchemy import SQLAlchemyModelFactory
from faker import Faker

from dbmodels.src import models
from dbmodels.src.models import Status

db_session = MagicMock()
faker = Faker()


def lazy(func: Callable, *args, **kwargs):
    """Wrap a callable so factory_boy evaluates it lazily (per instance)."""
    return lazy_attribute(lambda _: func(*args, **kwargs))


class UserFactory(SQLAlchemyModelFactory):
    """Factory for creating User model instances in tests."""

    class Meta:
        model = models.User
        sqlalchemy_session = db_session

    id = lazy(uuid4)
    username = lazy(lambda: faker.pystr(max_chars=128))
    email_address = lazy(faker.email)
    processing_state = Status.new
    created = lazy(faker.date_time_this_year)
    updated = None


class ClickFactory(SQLAlchemyModelFactory):
    """Factory for creating Click model instances in tests."""

    class Meta:
        model = models.Click
        sqlalchemy_session = db_session

    id = lazy(uuid4)
    user_id = lazy(uuid4)  # override in test with user.id
    shop_url = lazy(faker.url)
    click_timestamp = lazy(faker.date_time_this_year)
    created = lazy(faker.date_time_this_year)
