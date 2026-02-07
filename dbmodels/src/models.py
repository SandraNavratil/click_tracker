"""SQLAlchemy declarative models and enums."""

import enum
from datetime import datetime
from uuid import UUID, uuid4
from typing import ClassVar, Any
import sqlalchemy.types
from sqlalchemy import Enum, ForeignKey, String, func
from sqlalchemy.dialects.postgresql import UUID as PG_UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import JSONB, ARRAY


class Status(str, enum.Enum):
    """Processing state for a user record."""

    new = "new"
    queued = "queued"
    done = "done"


class Base(DeclarativeBase):
    """Modern SQLAlchemy 2.0 declarative base with comprehensive type mapping."""

    type_annotation_map: ClassVar[dict[type, Any]] = {
        dict[str, Any]: JSONB,
        str: sqlalchemy.types.TEXT,
        list[str]: ARRAY(String),
    }


class User(Base):
    """One row per user, one user can have many clicks."""

    __tablename__ = "users"

    id: Mapped[UUID] = mapped_column(PG_UUID(as_uuid=True), primary_key=True)
    username: Mapped[str | None] = mapped_column(
        String(128), default=None, nullable=True
    )
    email_address: Mapped[str | None] = mapped_column(default=None, nullable=True)
    processing_state: Mapped[Status] = mapped_column(
        Enum(Status), index=True, default=Status.new, nullable=False
    )
    created: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)
    updated: Mapped[datetime | None] = mapped_column(onupdate=func.now(), nullable=True)

    clicks: Mapped[list["Click"]] = relationship(back_populates="user")


class Click(Base):
    """One row per click, one click belongs to one user."""

    __tablename__ = "clicks"

    id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), primary_key=True, default=uuid4
    )
    user_id: Mapped[UUID] = mapped_column(
        PG_UUID(as_uuid=True), ForeignKey("users.id"), nullable=False
    )
    shop_url: Mapped[str] = mapped_column(nullable=False)
    click_timestamp: Mapped[datetime] = mapped_column(nullable=False)
    created: Mapped[datetime] = mapped_column(server_default=func.now(), nullable=False)

    user: Mapped["User"] = relationship(
        back_populates="clicks", lazy="joined", innerjoin=True
    )
