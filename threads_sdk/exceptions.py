"""Custom exceptions for threads-sdk."""


class ThreadsError(Exception):
    """Base exception for all threads-sdk errors."""


class AuthenticationError(ThreadsError):
    """Raised when authentication fails (invalid/expired token)."""


class RateLimitError(ThreadsError):
    """Raised when the API rate limit is exceeded."""

    def __init__(self, message: str, retry_after: int = 0) -> None:
        super().__init__(message)
        self.retry_after = retry_after


class NotFoundError(ThreadsError):
    """Raised when a resource is not found."""


class ValidationError(ThreadsError):
    """Raised when request validation fails."""
