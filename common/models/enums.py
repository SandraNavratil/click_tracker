"""Enums for user processing state and application environment."""

from enum import StrEnum, auto


# -- User processing state --
class ProcessingStatus(StrEnum):
    """Lifecycle state of a user."""

    new = auto()
    queued = auto()
    done = auto()


# -- Settings --
class EnvironmentEnum(StrEnum):
    """Deployment environment (local, test, sandbox, production)."""

    local = auto()
    test = auto()
    sandbox = auto()
    production = auto()
