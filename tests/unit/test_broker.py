"""Unit tests for broker."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from interposition.errors import InteractionNotFoundError
from interposition.models import (
    Cassette,
    ResponseChunk,
)
from interposition.services import Broker

if TYPE_CHECKING:
    from tests.unit.conftest import MakeInteractionProtocol, MakeRequestProtocol


class TestBroker:
    """Test suite for Broker."""

    def test_creates_with_cassette(self) -> None:
        """Test that Broker can be created with a cassette."""
        cassette = Cassette(interactions=())
        broker = Broker(cassette=cassette)

        assert broker.cassette == cassette

    def test_creates_with_mode_parameter(self) -> None:
        """Test that Broker can be created with a mode parameter."""
        cassette = Cassette(interactions=())
        broker = Broker(cassette=cassette, mode="replay")

        assert broker.mode == "replay"

    def test_replay_returns_chunks_for_matching_request(
        self, make_interaction: MakeInteractionProtocol
    ) -> None:
        """Test that replay returns chunks when request matches."""
        expected_chunk_count = 2
        interaction = make_interaction(
            response_chunks=(
                ResponseChunk(data=b"chunk1", sequence=0),
                ResponseChunk(data=b"chunk2", sequence=1),
            )
        )
        cassette = Cassette(interactions=(interaction,))
        broker = Broker(cassette=cassette)

        chunks = list(broker.replay(interaction.request))

        assert len(chunks) == expected_chunk_count
        assert chunks[0].data == b"chunk1"
        assert chunks[0].sequence == 0
        assert chunks[1].data == b"chunk2"
        assert chunks[1].sequence == 1

    def test_replay_raises_error_for_non_matching_request(
        self,
        make_request: MakeRequestProtocol,
        make_interaction: MakeInteractionProtocol,
    ) -> None:
        """Test that replay raises InteractionNotFoundError for non-matching request."""
        interaction = make_interaction()
        cassette = Cassette(interactions=(interaction,))
        broker = Broker(cassette=cassette)

        different_request = make_request(action="store")  # Different action

        with pytest.raises(
            InteractionNotFoundError, match="No matching interaction for"
        ):
            list(broker.replay(different_request))

    def test_replay_preserves_chunk_ordering(
        self, make_interaction: MakeInteractionProtocol
    ) -> None:
        """Test that replay preserves original chunk ordering."""
        interaction = make_interaction(
            response_chunks=(
                ResponseChunk(data=b"first", sequence=0),
                ResponseChunk(data=b"second", sequence=1),
                ResponseChunk(data=b"third", sequence=2),
            )
        )
        cassette = Cassette(interactions=(interaction,))
        broker = Broker(cassette=cassette)

        chunks = list(broker.replay(interaction.request))

        assert chunks[0].data == b"first"
        assert chunks[1].data == b"second"
        assert chunks[2].data == b"third"

    def test_replay_returns_iterator(
        self, make_interaction: MakeInteractionProtocol
    ) -> None:
        """Test that replay returns an iterator (lazy evaluation)."""
        interaction = make_interaction()
        cassette = Cassette(interactions=(interaction,))
        broker = Broker(cassette=cassette)

        result = broker.replay(interaction.request)

        # Should be an iterator, not a list/tuple
        assert hasattr(result, "__iter__")
        assert hasattr(result, "__next__")

    def test_replay_with_single_chunk(
        self, make_interaction: MakeInteractionProtocol
    ) -> None:
        """Test replay with single-chunk response."""
        interaction = make_interaction(
            response_chunks=(ResponseChunk(data=b"complete", sequence=0),)
        )
        cassette = Cassette(interactions=(interaction,))
        broker = Broker(cassette=cassette)

        chunks = list(broker.replay(interaction.request))

        assert len(chunks) == 1
        assert chunks[0].data == b"complete"


class TestInteractionNotFoundError:
    """Test suite for InteractionNotFoundError."""

    def test_stores_request(self, make_request: MakeRequestProtocol) -> None:
        """Test that exception stores the request."""
        request = make_request()
        error = InteractionNotFoundError(request)

        assert error.request == request

    def test_error_message_includes_request_info(
        self, make_request: MakeRequestProtocol
    ) -> None:
        """Test that error message includes request information."""
        request = make_request()
        error = InteractionNotFoundError(request)

        message = str(error)
        assert "test-proto" in message
        assert "fetch" in message
        assert "resource-123" in message
