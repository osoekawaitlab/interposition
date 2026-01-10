"""Unit tests for Pydantic serialization and deserialization."""

from __future__ import annotations

import json

import pytest
from pydantic import ValidationError

from interposition.models import (
    Cassette,
    Interaction,
    InteractionRequest,
    RequestFingerprint,
    ResponseChunk,
)


class TestResponseChunkSerialization:
    """Test suite for ResponseChunk serialization."""

    def test_model_dump_returns_dict(self) -> None:
        """Test that model_dump returns a dictionary."""
        chunk = ResponseChunk(data=b"test", sequence=0, metadata=(("key", "value"),))

        result = chunk.model_dump()

        assert isinstance(result, dict)
        assert result["data"] == b"test"
        assert result["sequence"] == 0
        assert result["metadata"] == (("key", "value"),)

    def test_model_dump_json_returns_json_string(self) -> None:
        """Test that model_dump_json returns a JSON string."""
        chunk = ResponseChunk(data=b"test", sequence=0)

        result = chunk.model_dump_json()

        assert isinstance(result, str)
        parsed = json.loads(result)
        assert parsed["sequence"] == 0

    def test_model_validate_deserializes_from_dict(self) -> None:
        """Test that model_validate deserializes from dict."""
        data = {"data": b"test", "sequence": 0, "metadata": ()}

        chunk = ResponseChunk.model_validate(data)

        assert chunk.data == b"test"
        assert chunk.sequence == 0
        assert chunk.metadata == ()

    def test_model_validate_json_deserializes_from_json(self) -> None:
        """Test that model_validate_json deserializes from JSON."""
        # Create a chunk and serialize it to get correct JSON format
        original = ResponseChunk(data=b"test", sequence=1)
        json_str = original.model_dump_json()

        chunk = ResponseChunk.model_validate_json(json_str)

        assert chunk.data == b"test"
        assert chunk.sequence == 1

    def test_roundtrip_serialization(self) -> None:
        """Test that serialization and deserialization roundtrip correctly."""
        original = ResponseChunk(data=b"test", sequence=0, metadata=(("k", "v"),))

        json_str = original.model_dump_json()
        restored = ResponseChunk.model_validate_json(json_str)

        assert restored.data == original.data
        assert restored.sequence == original.sequence
        assert restored.metadata == original.metadata


class TestInteractionRequestSerialization:
    """Test suite for InteractionRequest serialization."""

    def test_model_dump_returns_dict(self) -> None:
        """Test that model_dump returns a dictionary."""
        request = InteractionRequest(
            protocol="http",
            action="GET",
            target="/api",
            headers=(("Host", "example.com"),),
            body=b"",
        )

        result = request.model_dump()

        assert isinstance(result, dict)
        assert result["protocol"] == "http"
        assert result["action"] == "GET"
        assert result["target"] == "/api"

    def test_model_validate_json_deserializes_from_json(self) -> None:
        """Test that model_validate_json deserializes from JSON."""
        json_str = (
            '{"protocol":"http","action":"GET","target":"/api",'
            '"headers":[["Host","example.com"]],"body":""}'
        )

        request = InteractionRequest.model_validate_json(json_str)

        assert request.protocol == "http"
        assert request.action == "GET"
        assert request.target == "/api"

    def test_roundtrip_serialization(self) -> None:
        """Test that serialization and deserialization roundtrip correctly."""
        original = InteractionRequest(
            protocol="http",
            action="POST",
            target="/api",
            headers=(("Content-Type", "application/json"),),
            body=b'{"key":"value"}',
        )

        json_str = original.model_dump_json()
        restored = InteractionRequest.model_validate_json(json_str)

        assert restored.protocol == original.protocol
        assert restored.action == original.action
        assert restored.target == original.target
        assert restored.headers == original.headers
        assert restored.body == original.body


class TestRequestFingerprintSerialization:
    """Test suite for RequestFingerprint serialization."""

    def test_model_dump_returns_dict(self) -> None:
        """Test that model_dump returns a dictionary."""
        fingerprint = RequestFingerprint(value="abc123")

        result = fingerprint.model_dump()

        assert isinstance(result, dict)
        assert result["value"] == "abc123"

    def test_roundtrip_serialization(self) -> None:
        """Test that serialization and deserialization roundtrip correctly."""
        original = RequestFingerprint(value="abc123")

        json_str = original.model_dump_json()
        restored = RequestFingerprint.model_validate_json(json_str)

        assert restored.value == original.value


class TestInteractionSerialization:
    """Test suite for Interaction serialization."""

    def test_model_dump_returns_dict(self) -> None:
        """Test that model_dump returns a dictionary."""
        request = InteractionRequest(
            protocol="http",
            action="GET",
            target="/api",
            headers=(),
            body=b"",
        )
        interaction = Interaction(
            request=request,
            fingerprint=request.fingerprint(),
            response_chunks=(ResponseChunk(data=b"response", sequence=0),),
        )

        result = interaction.model_dump()

        assert isinstance(result, dict)
        assert "request" in result
        assert "fingerprint" in result
        assert "response_chunks" in result

    def test_roundtrip_serialization(self) -> None:
        """Test that serialization and deserialization roundtrip correctly."""
        request = InteractionRequest(
            protocol="http",
            action="GET",
            target="/api",
            headers=(("Host", "example.com"),),
            body=b"",
        )
        original = Interaction(
            request=request,
            fingerprint=request.fingerprint(),
            response_chunks=(
                ResponseChunk(data=b"chunk1", sequence=0),
                ResponseChunk(data=b"chunk2", sequence=1),
            ),
            metadata=(("key", "value"),),
        )

        json_str = original.model_dump_json()
        restored = Interaction.model_validate_json(json_str)

        assert restored.request.protocol == original.request.protocol
        assert restored.request.action == original.request.action
        assert restored.fingerprint.value == original.fingerprint.value
        assert len(restored.response_chunks) == len(original.response_chunks)
        assert restored.response_chunks[0].data == original.response_chunks[0].data
        assert restored.metadata == original.metadata

    def test_deserialization_validates_fingerprint(self) -> None:
        """Test that deserialization validates fingerprint matches request."""
        request = InteractionRequest(
            protocol="http",
            action="GET",
            target="/api",
            headers=(),
            body=b"",
        )
        # Create valid interaction first
        valid_interaction = Interaction(
            request=request,
            fingerprint=request.fingerprint(),
            response_chunks=(ResponseChunk(data=b"test", sequence=0),),
        )

        # Get JSON and modify fingerprint to be invalid
        data = json.loads(valid_interaction.model_dump_json())
        data["fingerprint"]["value"] = "invalid-fingerprint"
        json_str = json.dumps(data)

        # Should raise Pydantic ValidationError (wrapping our domain error)
        with pytest.raises(ValidationError, match="Fingerprint does not match"):
            Interaction.model_validate_json(json_str)


class TestCassetteSerialization:
    """Test suite for Cassette serialization."""

    def test_model_dump_returns_dict(self) -> None:
        """Test that model_dump returns a dictionary."""
        request = InteractionRequest(
            protocol="http",
            action="GET",
            target="/api",
            headers=(),
            body=b"",
        )
        interaction = Interaction(
            request=request,
            fingerprint=request.fingerprint(),
            response_chunks=(ResponseChunk(data=b"response", sequence=0),),
        )
        cassette = Cassette(interactions=(interaction,))

        result = cassette.model_dump()

        assert isinstance(result, dict)
        assert "interactions" in result
        assert len(result["interactions"]) == 1

    def test_private_index_excluded_from_serialization(self) -> None:
        """Test that _index private attribute is excluded from serialization."""
        request = InteractionRequest(
            protocol="http",
            action="GET",
            target="/api",
            headers=(),
            body=b"",
        )
        interaction = Interaction(
            request=request,
            fingerprint=request.fingerprint(),
            response_chunks=(ResponseChunk(data=b"response", sequence=0),),
        )
        cassette = Cassette(interactions=(interaction,))

        result = cassette.model_dump()

        assert "_index" not in result

        json_str = cassette.model_dump_json()
        assert "_index" not in json_str

    def test_roundtrip_serialization(self) -> None:
        """Test that serialization and deserialization roundtrip correctly."""
        request1 = InteractionRequest(
            protocol="http",
            action="GET",
            target="/api/1",
            headers=(),
            body=b"",
        )
        request2 = InteractionRequest(
            protocol="http",
            action="GET",
            target="/api/2",
            headers=(),
            body=b"",
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
        original = Cassette(interactions=(interaction1, interaction2))

        json_str = original.model_dump_json()
        restored = Cassette.model_validate_json(json_str)

        assert len(restored.interactions) == len(original.interactions)
        assert (
            restored.interactions[0].request.target
            == original.interactions[0].request.target
        )
        assert (
            restored.interactions[1].request.target
            == original.interactions[1].request.target
        )

    def test_deserialized_cassette_rebuilds_index(self) -> None:
        """Test that deserialized cassette rebuilds index for find_interaction."""
        request = InteractionRequest(
            protocol="http",
            action="GET",
            target="/api",
            headers=(),
            body=b"",
        )
        interaction = Interaction(
            request=request,
            fingerprint=request.fingerprint(),
            response_chunks=(ResponseChunk(data=b"response", sequence=0),),
        )
        original = Cassette(interactions=(interaction,))

        json_str = original.model_dump_json()
        restored = Cassette.model_validate_json(json_str)

        # Index should be rebuilt and functional
        found = restored.find_interaction(request.fingerprint())
        assert found is not None
        assert found.request.target == request.target


class TestSchemaGeneration:
    """Test suite for JSON schema generation."""

    def test_response_chunk_schema_generation(self) -> None:
        """Test that ResponseChunk can generate JSON schema."""
        schema = ResponseChunk.model_json_schema()

        assert isinstance(schema, dict)
        assert "properties" in schema
        assert "data" in schema["properties"]
        assert "sequence" in schema["properties"]

    def test_interaction_request_schema_generation(self) -> None:
        """Test that InteractionRequest can generate JSON schema."""
        schema = InteractionRequest.model_json_schema()

        assert isinstance(schema, dict)
        assert "properties" in schema
        assert "protocol" in schema["properties"]
        assert "action" in schema["properties"]
        assert "target" in schema["properties"]

    def test_cassette_schema_generation(self) -> None:
        """Test that Cassette can generate JSON schema."""
        schema = Cassette.model_json_schema()

        assert isinstance(schema, dict)
        assert "properties" in schema
        assert "interactions" in schema["properties"]
        # Verify _index is not in schema
        assert "_index" not in schema["properties"]
