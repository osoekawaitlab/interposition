"""Data models for interposition."""

from __future__ import annotations

import hashlib
import json

from pydantic import BaseModel, ConfigDict, PrivateAttr, model_validator
from typing_extensions import Self


class InteractionValidationError(ValueError):
    """Raised when interaction validation fails."""


class ResponseChunk(BaseModel):
    """Discrete piece of response data.

    Attributes:
        data: Chunk payload as bytes
        sequence: Zero-based chunk position in response stream
        metadata: Optional chunk-specific metadata as key-value pairs
    """

    model_config = ConfigDict(frozen=True)

    data: bytes
    sequence: int
    metadata: tuple[tuple[str, str], ...] = ()


class InteractionRequest(BaseModel):
    """Structured representation of a protocol-agnostic request.

    Attributes:
        protocol: Protocol identifier (e.g., "grpc", "graphql", "mqtt")
        action: Action/method name (e.g., "ListUsers", "query", "publish")
        target: Target resource (e.g., "users.UserService", "topic/sensors")
        headers: Request headers as immutable sequence of key-value pairs
        body: Request body content as bytes
    """

    model_config = ConfigDict(frozen=True)

    protocol: str
    action: str
    target: str
    headers: tuple[tuple[str, str], ...]
    body: bytes

    def fingerprint(self) -> RequestFingerprint:
        """Generate stable fingerprint for efficient matching.

        Returns:
            RequestFingerprint derived from all request fields.
        """
        return RequestFingerprint.from_request(self)


class RequestFingerprint(BaseModel):
    """Stable unique identifier for request matching.

    Attributes:
        value: SHA-256 hash of canonicalized request fields
    """

    model_config = ConfigDict(frozen=True)

    value: str

    @classmethod
    def from_request(cls, request: InteractionRequest) -> Self:
        """Create fingerprint from InteractionRequest.

        Args:
            request: The request to fingerprint

        Returns:
            RequestFingerprint with SHA-256 hash value
        """
        # Canonical order: protocol, action, target, sorted_headers, body
        sorted_headers = tuple(sorted(request.headers))
        canonical_data = [
            request.protocol,
            request.action,
            request.target,
            sorted_headers,
            request.body.hex(),
        ]
        canonical = json.dumps(canonical_data, separators=(",", ":"), sort_keys=True)
        hash_value = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
        return cls(value=hash_value)


class Interaction(BaseModel):
    """Complete request-response pair for replay.

    Attributes:
        request: The original InteractionRequest
        fingerprint: Precomputed request fingerprint for matching
        response_chunks: Ordered sequence of response chunks
        metadata: Optional interaction-level metadata as key-value pairs
    """

    model_config = ConfigDict(frozen=True)

    request: InteractionRequest
    fingerprint: RequestFingerprint
    response_chunks: tuple[ResponseChunk, ...]
    metadata: tuple[tuple[str, str], ...] = ()

    @model_validator(mode="after")
    def validate_interaction(self) -> Self:
        """Validate interaction integrity.

        Raises:
            InteractionValidationError: If fingerprint doesn't match request
                or chunks aren't sequential
        """
        # Verify fingerprint matches request
        expected_fingerprint = self.request.fingerprint()
        if self.fingerprint != expected_fingerprint:
            msg = (
                f"Fingerprint does not match request: "
                f"expected {expected_fingerprint.value}, got {self.fingerprint.value}"
            )
            raise InteractionValidationError(msg)

        # Verify response chunks are sequentially ordered
        if not self.response_chunks:
            msg = "Response chunks cannot be empty"
            raise InteractionValidationError(msg)

        if self.response_chunks[0].sequence != 0:
            msg = "Response chunks must start at sequence 0"
            raise InteractionValidationError(msg)

        for i, chunk in enumerate(self.response_chunks):
            if chunk.sequence != i:
                msg = "Response chunks must be sequential with no gaps"
                raise InteractionValidationError(msg)

        return self


class Cassette(BaseModel):
    """In-memory collection of recorded interactions.

    Attributes:
        interactions: Ordered sequence of interactions
    """

    model_config = ConfigDict(frozen=True)

    interactions: tuple[Interaction, ...]
    _index: dict[RequestFingerprint, int] = PrivateAttr(default_factory=dict)

    @model_validator(mode="after")
    def build_index(self) -> Self:
        """Build fingerprint index for efficient lookup."""
        index: dict[RequestFingerprint, int] = {}
        for i, interaction in enumerate(self.interactions):
            # Only store first occurrence of each fingerprint
            if interaction.fingerprint not in index:
                index[interaction.fingerprint] = i
        # Use object.__setattr__ to modify frozen model
        object.__setattr__(self, "_index", index)
        return self

    def find_interaction(self, fingerprint: RequestFingerprint) -> Interaction | None:
        """Find first interaction matching fingerprint.

        Args:
            fingerprint: Request fingerprint to search for

        Returns:
            Matching Interaction or None if not found
        """
        position = self._index.get(fingerprint)
        if position is None:
            return None
        return self.interactions[position]
