"""Unit tests for cassette structures."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from interposition.models import (
    Cassette,
    Interaction,
    InteractionRequest,
    ResponseChunk,
)

if TYPE_CHECKING:
    from tests.unit.conftest import MakeInteractionProtocol


class TestCassette:
    """Test suite for Cassette."""

    def test_creates_with_interactions(
        self, make_interaction: MakeInteractionProtocol
    ) -> None:
        """Test that Cassette can be created with interactions."""
        interaction = make_interaction()

        cassette = Cassette(interactions=(interaction,))

        assert cassette.interactions == (interaction,)
        assert len(cassette.interactions) == 1

    def test_is_frozen(self, make_interaction: MakeInteractionProtocol) -> None:
        """Test that Cassette is immutable."""
        interaction = make_interaction()
        cassette = Cassette(interactions=(interaction,))

        with pytest.raises(ValidationError, match="frozen"):
            cassette.interactions = ()  # type: ignore[misc]

    def test_find_interaction_returns_match(self) -> None:
        """Test that find_interaction returns matching interaction."""
        request = InteractionRequest(
            protocol="test-proto",
            action="fetch",
            target="resource-123",
            headers=(),
            body=b"",
        )
        interaction = Interaction(
            request=request,
            fingerprint=request.fingerprint(),
            response_chunks=(ResponseChunk(data=b"test", sequence=0),),
        )
        cassette = Cassette(interactions=(interaction,))

        found = cassette.find_interaction(request.fingerprint())

        assert found == interaction

    def test_find_interaction_returns_none_when_no_match(self) -> None:
        """Test that find_interaction returns None when no match exists."""
        request1 = InteractionRequest(
            protocol="test-proto",
            action="fetch",
            target="resource-123",
            headers=(),
            body=b"",
        )
        interaction = Interaction(
            request=request1,
            fingerprint=request1.fingerprint(),
            response_chunks=(ResponseChunk(data=b"test", sequence=0),),
        )
        cassette = Cassette(interactions=(interaction,))

        request2 = InteractionRequest(
            protocol="test-proto",
            action="store",  # Different action
            target="resource-123",
            headers=(),
            body=b"",
        )

        found = cassette.find_interaction(request2.fingerprint())

        assert found is None

    def test_find_interaction_returns_first_match(self) -> None:
        """Test that find_interaction returns first matching interaction."""
        request = InteractionRequest(
            protocol="test-proto",
            action="fetch",
            target="resource-123",
            headers=(),
            body=b"",
        )
        interaction1 = Interaction(
            request=request,
            fingerprint=request.fingerprint(),
            response_chunks=(ResponseChunk(data=b"first", sequence=0),),
        )
        interaction2 = Interaction(
            request=request,
            fingerprint=request.fingerprint(),
            response_chunks=(ResponseChunk(data=b"second", sequence=0),),
        )
        cassette = Cassette(interactions=(interaction1, interaction2))

        found = cassette.find_interaction(request.fingerprint())

        assert found == interaction1
        assert found is not interaction2

    def test_supports_empty_cassette(self) -> None:
        """Test that Cassette can be created with no interactions."""
        cassette = Cassette(interactions=())

        assert cassette.interactions == ()
        assert len(cassette.interactions) == 0

    def test_find_interaction_in_empty_cassette_returns_none(self) -> None:
        """Test that find_interaction returns None for empty cassette."""
        cassette = Cassette(interactions=())
        request = InteractionRequest(
            protocol="test-proto",
            action="fetch",
            target="resource-123",
            headers=(),
            body=b"",
        )

        found = cassette.find_interaction(request.fingerprint())

        assert found is None

    def test_supports_multiple_interactions(self) -> None:
        """Test that Cassette supports multiple different interactions."""
        request1 = InteractionRequest(
            protocol="test-proto",
            action="fetch",
            target="resource-1",
            headers=(),
            body=b"",
        )
        request2 = InteractionRequest(
            protocol="test-proto",
            action="store",
            target="resource-2",
            headers=(),
            body=b"data",
        )
        interaction1 = Interaction(
            request=request1,
            fingerprint=request1.fingerprint(),
            response_chunks=(ResponseChunk(data=b"response1", sequence=0),),
        )
        interaction2 = Interaction(
            request=request2,
            fingerprint=request2.fingerprint(),
            response_chunks=(ResponseChunk(data=b"response2", sequence=0),),
        )

        cassette = Cassette(interactions=(interaction1, interaction2))

        assert cassette.find_interaction(request1.fingerprint()) == interaction1
        assert cassette.find_interaction(request2.fingerprint()) == interaction2
