"""Exceptions for interposition."""

from __future__ import annotations

from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from interposition.models import InteractionRequest


class InteractionNotFoundError(Exception):
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
