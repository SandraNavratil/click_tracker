"""Domain and validation exceptions used across the application."""


class UnexpectedParameterValue(Exception):
    """Raised when a request parameter has an unexpected or invalid value."""

    ...


class MissingRequiredAttribute(Exception):
    """Raised when a required context (e.g. session/transaction) is missing."""

    ...


class EntityNotFound(Exception):
    """Raised when a requested entity (e.g. user) does not exist."""

    def __init__(self, entity_name: str, entity_id: str | int) -> None:
        """Set entity name and id and build the exception message.

        Args:
            entity_name: Type of entity (e.g. "User").
            entity_id: Requested id that was not found.
        """
        self.entity_name = entity_name
        self.entity_id = entity_id
        super().__init__(f"{entity_name} with id {entity_id} not found")
