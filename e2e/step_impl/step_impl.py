"""Step implementations for Gauge tests."""

from typing import cast

from getgauge.python import data_store, step

from interposition import (
    Broker,
    Cassette,
    Interaction,
    InteractionNotFoundError,
    InteractionRequest,
    ResponseChunk,
)

# Replay functionality steps


@step("Create cassette with recorded interaction for <protocol> <action> <target>")
def create_cassette_with_interaction(protocol: str, action: str, target: str) -> None:
    """Create cassette with test interaction."""
    request = InteractionRequest(
        protocol=protocol,
        action=action,
        target=target,
        headers=(),
        body=b"test-data",
    )
    chunks = (
        ResponseChunk(data=b"response-part1", sequence=0),
        ResponseChunk(data=b"response-part2", sequence=1),
    )
    interaction = Interaction(
        request=request,
        fingerprint=request.fingerprint(),
        response_chunks=chunks,
    )
    cassette = Cassette(interactions=(interaction,))
    data_store.scenario["cassette"] = cassette
    data_store.scenario["expected_chunks"] = chunks


@step("Broker receives identical request for <protocol> <action> <target>")
def broker_receives_identical_request(protocol: str, action: str, target: str) -> None:
    """Send identical request to broker."""
    cassette = cast("Cassette", data_store.scenario["cassette"])
    broker = Broker(cassette=cassette)
    request = InteractionRequest(
        protocol=protocol,
        action=action,
        target=target,
        headers=(),
        body=b"test-data",
    )
    try:
        chunks = list(broker.replay(request))
        data_store.scenario["response_chunks"] = chunks
        data_store.scenario["error"] = None
    except InteractionNotFoundError as e:
        data_store.scenario["response_chunks"] = None
        data_store.scenario["error"] = e


@step("Broker receives different request for <protocol> <action> <target>")
def broker_receives_different_request(protocol: str, action: str, target: str) -> None:
    """Send different request to broker."""
    cassette = cast("Cassette", data_store.scenario["cassette"])
    broker = Broker(cassette=cassette)
    request = InteractionRequest(
        protocol=protocol,
        action=action,
        target=target,
        headers=(),
        body=b"different-data",
    )
    try:
        chunks = list(broker.replay(request))
        data_store.scenario["response_chunks"] = chunks
        data_store.scenario["error"] = None
    except InteractionNotFoundError as e:
        data_store.scenario["response_chunks"] = None
        data_store.scenario["error"] = e


@step("Response stream should contain recorded chunks in order")
def response_stream_contains_recorded_chunks() -> None:
    """Verify response chunks match expected."""
    response_chunks = cast(
        "list[ResponseChunk] | None", data_store.scenario.get("response_chunks")
    )
    expected_chunks = cast(
        "tuple[ResponseChunk, ...] | None", data_store.scenario.get("expected_chunks")
    )

    assert response_chunks is not None, "No response chunks received"
    assert expected_chunks is not None, "No expected chunks found"
    assert len(response_chunks) == len(expected_chunks), (
        f"Expected {len(expected_chunks)} chunks, got {len(response_chunks)}"
    )

    for i, (actual, expected) in enumerate(
        zip(response_chunks, expected_chunks, strict=False)
    ):
        assert actual.data == expected.data, (
            f"Chunk {i} data mismatch: expected {expected.data!r}, got {actual.data!r}"
        )
        assert actual.sequence == expected.sequence, (
            f"Chunk {i} sequence mismatch: "
            f"expected {expected.sequence}, got {actual.sequence}"
        )


@step("Response stream should complete without errors")
def response_stream_completes_without_errors() -> None:
    """Verify no errors occurred."""
    error = cast("InteractionNotFoundError | None", data_store.scenario.get("error"))
    assert error is None, f"Unexpected error: {error}"


@step("Broker should raise InteractionNotFoundError")
def broker_should_raise_error() -> None:
    """Verify InteractionNotFoundError was raised."""
    error = cast("InteractionNotFoundError | None", data_store.scenario.get("error"))
    assert error is not None, "Expected InteractionNotFoundError but got none"
    assert isinstance(error, InteractionNotFoundError), (
        f"Expected InteractionNotFoundError, got {type(error).__name__}"
    )


@step(
    "Create cassette with two identical interactions for <protocol> <action> <target>"
)
def create_cassette_with_two_identical_interactions(
    protocol: str, action: str, target: str
) -> None:
    """Create cassette with two identical interactions."""
    request = InteractionRequest(
        protocol=protocol,
        action=action,
        target=target,
        headers=(),
        body=b"test-data",
    )

    # First interaction
    chunks1 = (
        ResponseChunk(data=b"first-response-part1", sequence=0),
        ResponseChunk(data=b"first-response-part2", sequence=1),
    )
    interaction1 = Interaction(
        request=request,
        fingerprint=request.fingerprint(),
        response_chunks=chunks1,
    )

    # Second interaction (different response)
    chunks2 = (
        ResponseChunk(data=b"second-response-part1", sequence=0),
        ResponseChunk(data=b"second-response-part2", sequence=1),
    )
    interaction2 = Interaction(
        request=request,
        fingerprint=request.fingerprint(),
        response_chunks=chunks2,
    )

    cassette = Cassette(interactions=(interaction1, interaction2))
    data_store.scenario["cassette"] = cassette
    data_store.scenario["first_interaction_chunks"] = chunks1


@step("Broker receives request for <protocol> <action> <target>")
def broker_receives_request(protocol: str, action: str, target: str) -> None:
    """Send request to broker."""
    cassette = cast("Cassette", data_store.scenario["cassette"])
    broker = Broker(cassette=cassette)
    request = InteractionRequest(
        protocol=protocol,
        action=action,
        target=target,
        headers=(),
        body=b"test-data",
    )
    chunks = list(broker.replay(request))
    data_store.scenario["response_chunks"] = chunks


@step("Response stream should contain chunks from FIRST recorded interaction")
def response_stream_contains_first_interaction_chunks() -> None:
    """Verify response chunks are from first interaction."""
    response_chunks = cast(
        "list[ResponseChunk] | None", data_store.scenario.get("response_chunks")
    )
    first_chunks = cast(
        "tuple[ResponseChunk, ...] | None",
        data_store.scenario.get("first_interaction_chunks"),
    )

    assert response_chunks is not None, "No response chunks received"
    assert first_chunks is not None, "No expected chunks found"
    assert len(response_chunks) == len(first_chunks), (
        f"Expected {len(first_chunks)} chunks, got {len(response_chunks)}"
    )

    for i, (actual, expected) in enumerate(
        zip(response_chunks, first_chunks, strict=False)
    ):
        assert actual.data == expected.data, (
            f"Chunk {i} data mismatch: expected {expected.data!r}, got {actual.data!r}"
        )
        assert actual.sequence == expected.sequence, (
            f"Chunk {i} sequence mismatch: "
            f"expected {expected.sequence}, got {actual.sequence}"
        )
