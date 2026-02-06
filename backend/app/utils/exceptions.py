from __future__ import annotations


class EntityNotFoundError(Exception):
    """Raised when an entity cannot be found."""

    def __init__(self, entity: str, entity_id: int) -> None:
        self.entity = entity
        self.entity_id = entity_id


class ConfigValidationError(Exception):
    """Raised when config validation fails."""

    def __init__(self, detail: str) -> None:
        self.detail = detail


class ConfigSaveError(Exception):
    """Raised when persisting config fails."""

    def __init__(self, detail: str) -> None:
        self.detail = detail


class SpeechToTextUnavailableError(Exception):
    """Raised when speech-to-text service is unavailable."""

    def __init__(self, detail: str) -> None:
        self.detail = detail


class SpeechToTextOperationError(Exception):
    """Raised when a speech-to-text operation fails."""

    def __init__(self, detail: str) -> None:
        self.detail = detail
