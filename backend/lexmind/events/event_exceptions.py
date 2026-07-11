"""Event bus exceptions."""

from lexmind.exceptions import LexMindError


class EventBusError(LexMindError):
    """Base class for event bus errors."""


class HandlerError(EventBusError):
    """Raised when an event handler fails (wraps the original error)."""

    def __init__(self, handler_name: str, original: Exception) -> None:
        super().__init__(f"Handler '{handler_name}' failed: {original}")
        self.handler_name = handler_name
        self.original = original


class DuplicateHandlerError(EventBusError):
    """Raised when registering an already-registered handler."""


class UnknownEventError(EventBusError):
    """Raised when dispatching an unregistered event type."""
