"""Domain services for interposition."""

from __future__ import annotations

from collections.abc import Callable, Iterable
from typing import TYPE_CHECKING, Literal

from interposition.errors import InteractionNotFoundError, LiveResponderRequiredError
from interposition.models import Cassette, Interaction

if TYPE_CHECKING:
    from collections.abc import Iterator

    from interposition.models import InteractionRequest, ResponseChunk

BrokerMode = Literal["replay", "record", "auto"]
LiveResponder = Callable[["InteractionRequest"], "Iterable[ResponseChunk]"]


class Broker:
    """Manages interaction replay from cassettes.

    Attributes:
        cassette: The cassette containing recorded interactions
        mode: The broker mode (replay, record, or auto)
        live_responder: Optional callable for upstream forwarding
    """

    def __init__(
        self,
        cassette: Cassette,
        mode: BrokerMode = "replay",
        live_responder: LiveResponder | None = None,
    ) -> None:
        """Initialize broker with a cassette.

        Args:
            cassette: The cassette containing recorded interactions
            mode: The broker mode (replay, record, or auto)
            live_responder: Optional callable for upstream forwarding
        """
        self._cassette = cassette
        self._mode = mode
        self._live_responder = live_responder

    @property
    def cassette(self) -> Cassette:
        """Get the cassette."""
        return self._cassette

    @property
    def mode(self) -> BrokerMode:
        """Get the broker mode."""
        return self._mode

    @property
    def live_responder(self) -> LiveResponder | None:
        """Get the live responder."""
        return self._live_responder

    def replay(self, request: InteractionRequest) -> Iterator[ResponseChunk]:
        """Replay recorded response for matching request.

        Args:
            request: The request to match and replay

        Yields:
            ResponseChunks in original recorded order

        Raises:
            InteractionNotFoundError: When no matching interaction exists
                and mode is replay, or when mode is auto but no
                live_responder is configured.
            LiveResponderRequiredError: When mode is record but no
                live_responder is configured.
        """
        # record mode: always forward to live, ignore cassette
        if self._mode == "record":
            yield from self._forward_and_record(request)
            return

        # replay/auto mode: try cassette first
        interaction = self.cassette.find_interaction(request.fingerprint())
        if interaction is not None:
            yield from interaction.response_chunks
            return

        # MISS handling
        if self._mode == "replay":
            raise InteractionNotFoundError(request)

        # auto mode MISS: forward to live
        yield from self._forward_and_record(request)

    def _forward_and_record(
        self, request: InteractionRequest
    ) -> Iterator[ResponseChunk]:
        """Forward request to live responder and record the interaction.

        Args:
            request: The request to forward

        Yields:
            ResponseChunks from live responder

        Raises:
            LiveResponderRequiredError: When live_responder is not configured
                and mode is record.
            InteractionNotFoundError: When live_responder is not configured
                and mode is auto.
        """
        if self._live_responder is None:
            if self._mode == "record":
                raise LiveResponderRequiredError(self._mode)
            raise InteractionNotFoundError(request)

        chunks = tuple(self._live_responder(request))
        self._record_interaction(request, chunks)
        yield from chunks

    def _record_interaction(
        self,
        request: InteractionRequest,
        response_chunks: tuple[ResponseChunk, ...],
    ) -> None:
        """Record a new interaction to the cassette.

        Creates a new Cassette with the interaction appended.

        Args:
            request: The request that was made
            response_chunks: The response chunks from live responder
        """
        interaction = Interaction(
            request=request,
            fingerprint=request.fingerprint(),
            response_chunks=response_chunks,
        )
        new_interactions = (*self._cassette.interactions, interaction)
        self._cassette = Cassette(interactions=new_interactions)
