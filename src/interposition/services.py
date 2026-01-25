"""Domain services for interposition."""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from interposition.errors import InteractionNotFoundError

if TYPE_CHECKING:
    from collections.abc import Iterator

    from interposition.models import Cassette, InteractionRequest, ResponseChunk

BrokerMode = Literal["replay", "record", "auto"]


class Broker:
    """Manages interaction replay from cassettes.

    Attributes:
        cassette: The cassette containing recorded interactions
        mode: The broker mode (replay, record, or auto)
    """

    def __init__(self, cassette: Cassette, mode: BrokerMode = "replay") -> None:
        """Initialize broker with a cassette.

        Args:
            cassette: The cassette containing recorded interactions
            mode: The broker mode (replay, record, or auto)
        """
        self._cassette = cassette
        self._mode = mode

    @property
    def cassette(self) -> Cassette:
        """Get the cassette."""
        return self._cassette

    @property
    def mode(self) -> BrokerMode:
        """Get the broker mode."""
        return self._mode

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
