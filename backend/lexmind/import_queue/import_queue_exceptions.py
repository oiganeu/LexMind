"""Import queue exceptions."""
class ImportQueueError(Exception):
    """Base exception for the Import Queue."""


class InvalidRequestStateError(ImportQueueError):
    """Raised when attempting to transition a request to an invalid state."""


class DuplicateRequestError(ImportQueueError):
    """Raised when a duplicate import request is rejected by deduplication strategy."""


class InvalidPriorityError(ImportQueueError):
    """Raised when an invalid request priority is provided."""
