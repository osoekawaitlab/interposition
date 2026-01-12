"""Domain services for interposition."""

from __future__ import annotations

from typing import TYPE_CHECKING

from interposition.errors import InteractionNotFoundError

if TYPE_CHECKING:
    from collections.abc import Iterator

    from interposition.models import Cassette, InteractionRequest, ResponseChunk


class Broker:
    """Manages interaction replay from cassettes.

    Attributes:
        cassette: The cassette containing recorded interactions
    """

    def __init__(self, cassette: Cassette) -> None:
        """Initialize broker with a cassette.

        Args:
            cassette: The cassette containing recorded interactions
        """
        self._cassette = cassette

    @property
    def cassette(self) -> Cassette:
        """Get the cassette."""
        return self._cassette

    def replay(self, request: InteractionRequest) -> Iterator[ResponseChunk]:
        """Replay recorded response for matching request.

        Args:
            request: The request to match and replay

        Yields:
            ResponseChunks in original recorded order

        Raises:
            InteractionNotFoundError: When no matching interaction exists
        """
        fingerprint = request.fingerprint()
        interaction = self.cassette.find_interaction(fingerprint)

        if interaction is None:
            raise InteractionNotFoundError(request)

        yield from interaction.response_chunks
