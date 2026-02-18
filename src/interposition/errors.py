"""Exceptions for interposition."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from pathlib import Path

    from interposition.models import InteractionRequest


class InterpositionError(Exception):
    """Base class for all interposition exceptions."""


class InteractionNotFoundError(InterpositionError):
    """Raised when no matching interaction is found in cassette."""

    def __init__(self, request: InteractionRequest) -> None:
        """Initialize with request that failed to match.

        Args:
            request: The unmatched request
        """
        super().__init__(
            f"No matching interaction for {request.protocol}:"
            f"{request.action}:{request.target}"
        )
        self.request: InteractionRequest = request


class LiveResponderRequiredError(InterpositionError):
    """Raised when live_responder is required but not configured."""

    def __init__(self, mode: str) -> None:
        """Initialize with the mode that requires live_responder.

        Args:
            mode: The broker mode that requires live_responder
        """
        super().__init__(f"live_responder is required for {mode} mode")
        self.mode: str = mode


class CassetteLoadError(InterpositionError):
    """Raised when cassette loading fails."""

    def __init__(self, path: Path, cause: Exception) -> None:
        """Initialize with the path and underlying cause.

        Args:
            path: The file path where load failed
            cause: The underlying exception that caused the failure
        """
        super().__init__(f"Failed to load cassette from {path}: {cause}")
        self.path: Path = path
        self.__cause__ = cause


class CassetteSaveError(InterpositionError):
    """Raised when cassette persistence fails."""

    def __init__(self, path: Path, cause: Exception) -> None:
        """Initialize with the path and underlying cause.

        Args:
            path: The file path where save failed
            cause: The underlying exception that caused the failure
        """
        super().__init__(f"Failed to save cassette to {path}: {cause}")
        self.path: Path = path
        self.__cause__ = cause
