"""Unit tests for interaction structures."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from interposition.models import Interaction, InteractionRequest, ResponseChunk


class TestInteraction:
    """Test suite for Interaction."""

    def test_creates_with_all_fields(self) -> None:
        """Test that Interaction can be created with all fields."""
        request = InteractionRequest(
            protocol="test-proto",
            action="fetch",
            target="resource-123",
            headers=(),
            body=b"",
        )
        fingerprint = request.fingerprint()
        chunks = (
            ResponseChunk(data=b"part1", sequence=0),
            ResponseChunk(data=b"part2", sequence=1),
        )

        interaction = Interaction(
            request=request,
            fingerprint=fingerprint,
            response_chunks=chunks,
            metadata=(("timestamp", "2024-01-01"),),
        )

        assert interaction.request == request
        assert interaction.fingerprint == fingerprint
        assert interaction.response_chunks == chunks
        assert interaction.metadata == (("timestamp", "2024-01-01"),)

    def test_is_frozen(self) -> None:
        """Test that Interaction is immutable."""
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

        with pytest.raises(ValidationError, match="frozen"):
            interaction.request = request  # type: ignore[misc]

    def test_validates_fingerprint_matches_request(self) -> None:
        """Test that __post_init__ validates fingerprint matches request."""
        request = InteractionRequest(
            protocol="test-proto",
            action="fetch",
            target="resource-123",
            headers=(),
            body=b"",
        )
        wrong_request = InteractionRequest(
            protocol="other-proto",
            action="fetch",
            target="resource-123",
            headers=(),
            body=b"",
        )
        wrong_fingerprint = wrong_request.fingerprint()

        with pytest.raises(ValueError, match="Fingerprint does not match request"):
            Interaction(
                request=request,
                fingerprint=wrong_fingerprint,
                response_chunks=(ResponseChunk(data=b"test", sequence=0),),
            )

    def test_validates_chunk_sequences_start_at_zero(self) -> None:
        """Test that chunk sequences must start at 0."""
        request = InteractionRequest(
            protocol="test-proto",
            action="fetch",
            target="resource-123",
            headers=(),
            body=b"",
        )

        with pytest.raises(
            ValueError, match="Response chunks must start at sequence 0"
        ):
            Interaction(
                request=request,
                fingerprint=request.fingerprint(),
                response_chunks=(ResponseChunk(data=b"test", sequence=1),),
            )

    def test_validates_chunk_sequences_are_sequential(self) -> None:
        """Test that chunk sequences must be sequential with no gaps."""
        request = InteractionRequest(
            protocol="test-proto",
            action="fetch",
            target="resource-123",
            headers=(),
            body=b"",
        )

        with pytest.raises(
            ValueError, match="Response chunks must be sequential with no gaps"
        ):
            Interaction(
                request=request,
                fingerprint=request.fingerprint(),
                response_chunks=(
                    ResponseChunk(data=b"part1", sequence=0),
                    ResponseChunk(data=b"part3", sequence=2),  # Gap: missing sequence 1
                ),
            )

    def test_validates_response_chunks_not_empty(self) -> None:
        """Test that response_chunks cannot be empty."""
        request = InteractionRequest(
            protocol="test-proto",
            action="fetch",
            target="resource-123",
            headers=(),
            body=b"",
        )

        with pytest.raises(ValueError, match="Response chunks cannot be empty"):
            Interaction(
                request=request,
                fingerprint=request.fingerprint(),
                response_chunks=(),
            )

    def test_allows_single_chunk(self) -> None:
        """Test that single-chunk responses are valid."""
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
            response_chunks=(ResponseChunk(data=b"complete", sequence=0),),
        )

        assert len(interaction.response_chunks) == 1
        assert interaction.response_chunks[0].sequence == 0

    def test_allows_multi_chunk_response(self) -> None:
        """Test that multi-chunk responses are valid."""
        expected_chunk_count = 3
        last_chunk_index = 2
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
            response_chunks=(
                ResponseChunk(data=b"part1", sequence=0),
                ResponseChunk(data=b"part2", sequence=1),
                ResponseChunk(data=b"part3", sequence=last_chunk_index),
            ),
        )

        assert len(interaction.response_chunks) == expected_chunk_count
        assert interaction.response_chunks[0].sequence == 0
        assert interaction.response_chunks[1].sequence == 1
        assert (
            interaction.response_chunks[last_chunk_index].sequence == last_chunk_index
        )
