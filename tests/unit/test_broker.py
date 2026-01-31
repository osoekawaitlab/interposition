"""Unit tests for broker."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from interposition.errors import InteractionNotFoundError, LiveResponderRequiredError
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

    def test_creates_with_live_responder(self) -> None:
        """Test that Broker can be created with a live_responder."""
        cassette = Cassette(interactions=())

        def mock_responder(_request: object) -> tuple[ResponseChunk, ...]:
            return (ResponseChunk(data=b"response", sequence=0),)

        broker = Broker(cassette=cassette, live_responder=mock_responder)

        assert broker.live_responder is mock_responder

    def test_replay_forwards_to_live_responder_on_miss_in_auto_mode(
        self, make_request: MakeRequestProtocol
    ) -> None:
        """Test that auto mode forwards MISS to live_responder."""
        cassette = Cassette(interactions=())
        request = make_request()

        def mock_responder(_req: object) -> tuple[ResponseChunk, ...]:
            return (ResponseChunk(data=b"live-response", sequence=0),)

        broker = Broker(cassette=cassette, mode="auto", live_responder=mock_responder)

        chunks = list(broker.replay(request))

        assert len(chunks) == 1
        assert chunks[0].data == b"live-response"

    def test_replay_records_interaction_on_miss_in_auto_mode(
        self, make_request: MakeRequestProtocol
    ) -> None:
        """Test that auto mode records interaction to cassette on MISS."""
        cassette = Cassette(interactions=())
        request = make_request()

        def mock_responder(_req: object) -> tuple[ResponseChunk, ...]:
            return (ResponseChunk(data=b"live-response", sequence=0),)

        broker = Broker(cassette=cassette, mode="auto", live_responder=mock_responder)

        list(broker.replay(request))

        assert len(broker.cassette.interactions) == 1
        recorded = broker.cassette.interactions[0]
        assert recorded.request == request
        assert recorded.response_chunks[0].data == b"live-response"

    def test_replay_records_before_consumer_finishes_iterating(
        self, make_request: MakeRequestProtocol
    ) -> None:
        """Test that recording completes even if consumer stops early."""
        cassette = Cassette(interactions=())
        request = make_request()
        response_chunks = (
            ResponseChunk(data=b"chunk1", sequence=0),
            ResponseChunk(data=b"chunk2", sequence=1),
        )

        def mock_responder(_req: object) -> tuple[ResponseChunk, ...]:
            return response_chunks

        broker = Broker(cassette=cassette, mode="auto", live_responder=mock_responder)

        stream = broker.replay(request)
        next(stream)

        assert len(broker.cassette.interactions) == 1
        recorded = broker.cassette.interactions[0]
        assert len(recorded.response_chunks) == len(response_chunks)
        assert recorded.response_chunks[0].data == b"chunk1"
        assert recorded.response_chunks[1].data == b"chunk2"

    def test_replay_forwards_and_records_in_record_mode(
        self, make_request: MakeRequestProtocol
    ) -> None:
        """Test that record mode forwards MISS and records interaction."""
        cassette = Cassette(interactions=())
        request = make_request()

        def mock_responder(_req: object) -> tuple[ResponseChunk, ...]:
            return (ResponseChunk(data=b"recorded", sequence=0),)

        broker = Broker(cassette=cassette, mode="record", live_responder=mock_responder)

        chunks = list(broker.replay(request))

        assert chunks[0].data == b"recorded"
        assert len(broker.cassette.interactions) == 1

    def test_replay_always_forwards_to_live_in_record_mode_even_on_hit(
        self, make_interaction: MakeInteractionProtocol
    ) -> None:
        """Test that record mode forwards to live even when cassette has match."""
        interaction = make_interaction(
            response_chunks=(ResponseChunk(data=b"cached", sequence=0),)
        )
        cassette = Cassette(interactions=(interaction,))
        responder_called = False

        def mock_responder(_req: object) -> tuple[ResponseChunk, ...]:
            nonlocal responder_called
            responder_called = True
            return (ResponseChunk(data=b"fresh", sequence=0),)

        broker = Broker(cassette=cassette, mode="record", live_responder=mock_responder)

        chunks = list(broker.replay(interaction.request))

        assert responder_called is True
        assert chunks[0].data == b"fresh"

    def test_replay_raises_when_live_responder_missing_in_auto_mode(
        self, make_request: MakeRequestProtocol
    ) -> None:
        """Test that auto mode MISS raises without live responder."""
        cassette = Cassette(interactions=())
        request = make_request()
        broker = Broker(cassette=cassette, mode="auto")

        with pytest.raises(InteractionNotFoundError, match="No matching interaction"):
            list(broker.replay(request))

    def test_replay_raises_when_live_responder_missing_in_record_mode(
        self, make_request: MakeRequestProtocol
    ) -> None:
        """Test that record mode raises without live responder."""
        cassette = Cassette(interactions=())
        request = make_request()
        broker = Broker(cassette=cassette, mode="record")

        with pytest.raises(LiveResponderRequiredError, match="record mode"):
            list(broker.replay(request))

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


class TestBrokerCassetteStore:
    """Test suite for Broker with cassette_store."""

    def test_creates_with_cassette_store(self) -> None:
        """Test that Broker can be created with a cassette_store."""
        cassette = Cassette(interactions=())

        class MockStore:
            def load(self) -> Cassette:
                return Cassette(interactions=())

            def save(self, cassette: Cassette) -> None:
                pass

        store = MockStore()
        broker = Broker(cassette=cassette, cassette_store=store)

        assert broker.cassette_store is store

    def test_cassette_store_property_returns_none_when_not_configured(self) -> None:
        """Test that cassette_store property returns None when not set."""
        cassette = Cassette(interactions=())
        broker = Broker(cassette=cassette)

        assert broker.cassette_store is None

    def test_auto_save_called_on_miss_in_auto_mode(
        self, make_request: MakeRequestProtocol
    ) -> None:
        """Test that cassette_store.save is called on MISS in auto mode."""
        cassette = Cassette(interactions=())
        request = make_request()
        save_called_with: list[Cassette] = []

        class MockStore:
            def load(self) -> Cassette:
                return Cassette(interactions=())

            def save(self, cassette: Cassette) -> None:
                save_called_with.append(cassette)

        def mock_responder(_req: object) -> tuple[ResponseChunk, ...]:
            return (ResponseChunk(data=b"response", sequence=0),)

        broker = Broker(
            cassette=cassette,
            mode="auto",
            live_responder=mock_responder,
            cassette_store=MockStore(),
        )

        list(broker.replay(request))

        assert len(save_called_with) == 1
        assert len(save_called_with[0].interactions) == 1

    def test_auto_save_called_on_miss_in_record_mode(
        self, make_request: MakeRequestProtocol
    ) -> None:
        """Test that cassette_store.save is called on MISS in record mode."""
        cassette = Cassette(interactions=())
        request = make_request()
        save_called_with: list[Cassette] = []

        class MockStore:
            def load(self) -> Cassette:
                return Cassette(interactions=())

            def save(self, cassette: Cassette) -> None:
                save_called_with.append(cassette)

        def mock_responder(_req: object) -> tuple[ResponseChunk, ...]:
            return (ResponseChunk(data=b"response", sequence=0),)

        broker = Broker(
            cassette=cassette,
            mode="record",
            live_responder=mock_responder,
            cassette_store=MockStore(),
        )

        list(broker.replay(request))

        assert len(save_called_with) == 1
        assert len(save_called_with[0].interactions) == 1

    def test_no_save_on_hit_in_auto_mode(
        self, make_interaction: MakeInteractionProtocol
    ) -> None:
        """Test that cassette_store.save is NOT called on HIT in auto mode."""
        interaction = make_interaction()
        cassette = Cassette(interactions=(interaction,))
        save_called = False

        class MockStore:
            def load(self) -> Cassette:
                return Cassette(interactions=())

            def save(self, _cassette: Cassette) -> None:
                nonlocal save_called
                save_called = True

        def mock_responder(_req: object) -> tuple[ResponseChunk, ...]:
            return (ResponseChunk(data=b"response", sequence=0),)

        broker = Broker(
            cassette=cassette,
            mode="auto",
            live_responder=mock_responder,
            cassette_store=MockStore(),
        )

        list(broker.replay(interaction.request))

        assert save_called is False

    def test_save_receives_updated_cassette(
        self, make_request: MakeRequestProtocol
    ) -> None:
        """Test that save receives cassette with new interaction."""
        cassette = Cassette(interactions=())
        request = make_request()
        saved_cassette: Cassette | None = None

        class MockStore:
            def load(self) -> Cassette:
                return Cassette(interactions=())

            def save(self, cassette: Cassette) -> None:
                nonlocal saved_cassette
                saved_cassette = cassette

        def mock_responder(_req: object) -> tuple[ResponseChunk, ...]:
            return (ResponseChunk(data=b"live-data", sequence=0),)

        broker = Broker(
            cassette=cassette,
            mode="auto",
            live_responder=mock_responder,
            cassette_store=MockStore(),
        )

        list(broker.replay(request))

        assert saved_cassette is not None
        assert len(saved_cassette.interactions) == 1
        assert saved_cassette.interactions[0].request == request
        assert saved_cassette.interactions[0].response_chunks[0].data == b"live-data"

    def test_no_error_when_store_not_configured(
        self, make_request: MakeRequestProtocol
    ) -> None:
        """Test that recording works without cassette_store."""
        cassette = Cassette(interactions=())
        request = make_request()

        def mock_responder(_req: object) -> tuple[ResponseChunk, ...]:
            return (ResponseChunk(data=b"response", sequence=0),)

        broker = Broker(
            cassette=cassette,
            mode="auto",
            live_responder=mock_responder,
        )

        chunks = list(broker.replay(request))

        assert len(chunks) == 1
        assert len(broker.cassette.interactions) == 1


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
