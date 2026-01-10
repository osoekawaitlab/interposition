"""Unit tests for response structures."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from interposition.models import ResponseChunk


class TestResponseChunk:
    """Test suite for ResponseChunk."""

    def test_creates_with_required_fields(self) -> None:
        """Test that ResponseChunk can be created with required fields."""
        chunk = ResponseChunk(data=b"test data", sequence=0)

        assert chunk.data == b"test data"
        assert chunk.sequence == 0
        assert chunk.metadata == ()

    def test_is_frozen(self) -> None:
        """Test that ResponseChunk is immutable."""
        chunk = ResponseChunk(data=b"test data", sequence=0)

        with pytest.raises(ValidationError, match="frozen"):
            chunk.data = b"modified"  # type: ignore[misc]
