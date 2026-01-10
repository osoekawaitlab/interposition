"""Unit tests for request structures."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from interposition.models import InteractionRequest, RequestFingerprint


class TestInteractionRequest:
    """Test suite for InteractionRequest."""

    def test_creates_with_all_fields(self) -> None:
        """Test that InteractionRequest can be created with all fields."""
        request = InteractionRequest(
            protocol="test-proto",
            action="fetch",
            target="resource-123",
            headers=(("X-Custom", "value"), ("Content-Type", "application/json")),
            body=b'{"key": "value"}',
        )

        assert request.protocol == "test-proto"
        assert request.action == "fetch"
        assert request.target == "resource-123"
        assert request.headers == (
            ("X-Custom", "value"),
            ("Content-Type", "application/json"),
        )
        assert request.body == b'{"key": "value"}'

    def test_is_frozen(self) -> None:
        """Test that InteractionRequest is immutable."""
        request = InteractionRequest(
            protocol="test-proto",
            action="fetch",
            target="resource-123",
            headers=(),
            body=b"",
        )

        with pytest.raises(ValidationError, match="frozen"):
            request.protocol = "modified"  # type: ignore[misc]

    def test_fingerprint_is_stable(self) -> None:
        """Test that same request produces same fingerprint."""
        request = InteractionRequest(
            protocol="test-proto",
            action="fetch",
            target="resource-123",
            headers=(("X-Custom", "value"),),
            body=b"test",
        )

        fingerprint1 = request.fingerprint()
        fingerprint2 = request.fingerprint()

        assert fingerprint1 == fingerprint2
        assert fingerprint1.value == fingerprint2.value

    def test_different_requests_have_different_fingerprints(self) -> None:
        """Test that different requests produce different fingerprints."""
        request1 = InteractionRequest(
            protocol="test-proto",
            action="fetch",
            target="resource-123",
            headers=(),
            body=b"",
        )
        request2 = InteractionRequest(
            protocol="test-proto",
            action="store",  # Different action
            target="resource-123",
            headers=(),
            body=b"",
        )

        fingerprint1 = request1.fingerprint()
        fingerprint2 = request2.fingerprint()

        assert fingerprint1 != fingerprint2
        assert fingerprint1.value != fingerprint2.value


class TestRequestFingerprint:
    """Test suite for RequestFingerprint."""

    def test_from_request_produces_sha256(self) -> None:
        """Test that fingerprint uses SHA-256."""
        sha256_hex_length = 64  # SHA-256 produces 64 hex characters
        request = InteractionRequest(
            protocol="test-proto",
            action="fetch",
            target="resource-123",
            headers=(),
            body=b"",
        )

        fingerprint = RequestFingerprint.from_request(request)

        assert len(fingerprint.value) == sha256_hex_length
        assert all(c in "0123456789abcdef" for c in fingerprint.value)

    def test_fingerprint_includes_all_fields(self) -> None:
        """Test that changing any field changes fingerprint."""
        base_request = InteractionRequest(
            protocol="test-proto",
            action="fetch",
            target="resource-123",
            headers=(("X-Custom", "value"),),
            body=b"test",
        )
        base_fingerprint = RequestFingerprint.from_request(base_request)

        # Change protocol
        modified = InteractionRequest(
            protocol="other-proto",
            action="fetch",
            target="resource-123",
            headers=(("X-Custom", "value"),),
            body=b"test",
        )
        assert RequestFingerprint.from_request(modified) != base_fingerprint

        # Change action
        modified = InteractionRequest(
            protocol="test-proto",
            action="store",
            target="resource-123",
            headers=(("X-Custom", "value"),),
            body=b"test",
        )
        assert RequestFingerprint.from_request(modified) != base_fingerprint

        # Change target
        modified = InteractionRequest(
            protocol="test-proto",
            action="fetch",
            target="resource-456",
            headers=(("X-Custom", "value"),),
            body=b"test",
        )
        assert RequestFingerprint.from_request(modified) != base_fingerprint

        # Change headers
        modified = InteractionRequest(
            protocol="test-proto",
            action="fetch",
            target="resource-123",
            headers=(("X-Other", "value"),),
            body=b"test",
        )
        assert RequestFingerprint.from_request(modified) != base_fingerprint

        # Change body
        modified = InteractionRequest(
            protocol="test-proto",
            action="fetch",
            target="resource-123",
            headers=(("X-Custom", "value"),),
            body=b"different",
        )
        assert RequestFingerprint.from_request(modified) != base_fingerprint

    def test_is_frozen(self) -> None:
        """Test that RequestFingerprint is immutable."""
        fingerprint = RequestFingerprint(value="a" * 64)

        with pytest.raises(ValidationError, match="frozen"):
            fingerprint.value = "modified"  # type: ignore[misc]
