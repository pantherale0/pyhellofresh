"""Exception hierarchy for pyhellofresh."""

from __future__ import annotations

__all__ = [
    "HelloFreshAuthenticationError",
    "HelloFreshConnectionError",
    "HelloFreshError",
    "HelloFreshResponseError",
]


class HelloFreshError(Exception):
    """Base exception for all HelloFresh library errors."""


class HelloFreshAuthenticationError(HelloFreshError):
    """Raised when authentication fails, credentials/token missing/expired, or invalid_grant returned."""

    def __init__(
        self,
        message: str,
        status_code: int | None = None,
        error_code: str | None = None,
    ) -> None:
        super().__init__(message)
        self.status_code = status_code
        self.error_code = error_code


class HelloFreshResponseError(HelloFreshError):
    """Raised when the API returns an unexpected status code or malformed JSON."""

    def __init__(self, status_code: int, message: str) -> None:
        super().__init__(f"API Error [{status_code}]: {message}")
        self.status_code = status_code
        self.message = message


class HelloFreshConnectionError(HelloFreshError):
    """Raised on network issues or session timeouts."""
