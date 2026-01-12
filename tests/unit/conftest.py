"""Shared test fixtures for unit tests."""

from __future__ import annotations

from typing import Protocol

import pytest

from interposition.models import Interaction, InteractionRequest, ResponseChunk


class MakeRequestProtocol(Protocol):
    """Protocol for make_request fixture."""

    def __call__(
        self,
        protocol: str = "test-proto",
        action: str = "fetch",
        target: str = "resource-123",
        headers: tuple[tuple[str, str], ...] = (),
        body: bytes = b"",
    ) -> InteractionRequest:
        """Create an InteractionRequest with default values."""
        ...


class MakeChunkProtocol(Protocol):
    """Protocol for make_chunk fixture."""

    def __call__(
        self,
        data: bytes = b"test-data",
        sequence: int = 0,
        metadata: tuple[tuple[str, str], ...] = (),
    ) -> ResponseChunk:
        """Create a ResponseChunk with default values."""
        ...


class MakeInteractionProtocol(Protocol):
    """Protocol for make_interaction fixture."""

    def __call__(
        self,
        request: InteractionRequest | None = None,
        response_chunks: tuple[ResponseChunk, ...] | None = None,
        metadata: tuple[tuple[str, str], ...] = (),
    ) -> Interaction:
        """Create an Interaction with default values."""
        ...


@pytest.fixture
def make_request() -> MakeRequestProtocol:
    """Factory fixture for creating InteractionRequest objects with defaults."""

    def _make_request(
        protocol: str = "test-proto",
        action: str = "fetch",
        target: str = "resource-123",
        headers: tuple[tuple[str, str], ...] = (),
        body: bytes = b"",
    ) -> InteractionRequest:
        return InteractionRequest(
            protocol=protocol,
            action=action,
            target=target,
            headers=headers,
            body=body,
        )

    return _make_request


@pytest.fixture
def make_chunk() -> MakeChunkProtocol:
    """Factory fixture for creating ResponseChunk objects with defaults."""

    def _make_chunk(
        data: bytes = b"test-data",
        sequence: int = 0,
        metadata: tuple[tuple[str, str], ...] = (),
    ) -> ResponseChunk:
        return ResponseChunk(
            data=data,
            sequence=sequence,
            metadata=metadata,
        )

    return _make_chunk


@pytest.fixture
def make_interaction() -> MakeInteractionProtocol:
    """Factory fixture for creating Interaction objects with defaults."""

    def _make_interaction(
        request: InteractionRequest | None = None,
        response_chunks: tuple[ResponseChunk, ...] | None = None,
        metadata: tuple[tuple[str, str], ...] = (),
    ) -> Interaction:
        if request is None:
            request = InteractionRequest(
                protocol="test-proto",
                action="fetch",
                target="resource-123",
                headers=(),
                body=b"",
            )
        if response_chunks is None:
            response_chunks = (ResponseChunk(data=b"test-data", sequence=0),)

        return Interaction(
            request=request,
            fingerprint=request.fingerprint(),
            response_chunks=response_chunks,
            metadata=metadata,
        )

    return _make_interaction
