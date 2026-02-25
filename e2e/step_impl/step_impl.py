"""Step implementations for Gauge tests."""

import tempfile
from pathlib import Path
from typing import TYPE_CHECKING, cast

import pytest
from getgauge.python import after_scenario, data_store, step

from interposition import (
    Broker,
    BrokerMode,
    Cassette,
    CassetteLoadError,
    Interaction,
    InteractionNotFoundError,
    InteractionRequest,
    JsonFileCassetteStore,
    LiveResponderRequiredError,
    ResponseChunk,
)

if TYPE_CHECKING:
    from interposition.services import LiveResponder

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


@step("Broker should raise LiveResponderRequiredError")
def broker_should_raise_live_responder_required_error() -> None:
    """Verify LiveResponderRequiredError was raised."""
    error = cast(
        "InteractionNotFoundError | LiveResponderRequiredError | None",
        data_store.scenario.get("error"),
    )
    assert error is not None, "Expected LiveResponderRequiredError but got none"
    assert isinstance(error, LiveResponderRequiredError), (
        f"Expected LiveResponderRequiredError, got {type(error).__name__}"
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


def _parse_headers(header_text: str) -> tuple[tuple[str, str], ...]:
    """Parse comma-delimited header string into ordered header tuples."""
    if not header_text:
        return ()
    headers: list[tuple[str, str]] = []
    for part in header_text.split(","):
        name, value = part.split(":", 1)
        headers.append((name.strip(), value.strip()))
    return tuple(headers)


@step("Create cassette with recorded interaction headers <headers>")
def create_cassette_with_headers(headers: str) -> None:
    """Create cassette with headers in provided order."""
    request = InteractionRequest(
        protocol="test-proto",
        action="fetch",
        target="resource-123",
        headers=_parse_headers(headers),
        body=b"test-data",
    )
    chunks = (ResponseChunk(data=b"response", sequence=0),)
    interaction = Interaction(
        request=request,
        fingerprint=request.fingerprint(),
        response_chunks=chunks,
    )
    cassette = Cassette(interactions=(interaction,))
    data_store.scenario["cassette"] = cassette


@step("Broker receives request with headers <headers>")
def broker_receives_request_with_headers(headers: str) -> None:
    """Send request with header order to broker."""
    cassette = cast("Cassette", data_store.scenario["cassette"])
    broker = Broker(cassette=cassette)
    request = InteractionRequest(
        protocol="test-proto",
        action="fetch",
        target="resource-123",
        headers=_parse_headers(headers),
        body=b"test-data",
    )
    try:
        chunks = list(broker.replay(request))
        data_store.scenario["response_chunks"] = chunks
        data_store.scenario["error"] = None
    except InteractionNotFoundError as e:
        data_store.scenario["response_chunks"] = None
        data_store.scenario["error"] = e


# Record functionality steps


@step("Create empty cassette")
def create_empty_cassette() -> None:
    """Create an empty cassette with no interactions."""
    cassette = Cassette(interactions=())
    data_store.scenario["cassette"] = cassette


@step("Broker in <mode> mode receives request for <protocol> <action> <target>")
def broker_in_mode_receives_request(
    mode: str, protocol: str, action: str, target: str
) -> None:
    """Send request to broker with specified mode."""
    cassette = cast("Cassette", data_store.scenario["cassette"])
    live_responder = cast(
        "LiveResponder | None", data_store.scenario.get("live_responder")
    )
    try:
        broker = Broker(
            cassette=cassette,
            mode=cast("BrokerMode", mode),
            live_responder=live_responder,
        )
        request = InteractionRequest(
            protocol=protocol,
            action=action,
            target=target,
            headers=(),
            body=b"test-data",
        )
        chunks = list(broker.replay(request))
        data_store.scenario["response_chunks"] = chunks
        data_store.scenario["error"] = None
        # Update cassette reference after replay (may have been modified)
        data_store.scenario["cassette"] = broker.cassette
    except (InteractionNotFoundError, LiveResponderRequiredError) as e:
        data_store.scenario["response_chunks"] = None
        data_store.scenario["error"] = e


@step("Configure mock live responder returning <response_data>")
def configure_mock_live_responder(response_data: str) -> None:
    """Configure a mock live responder that returns the given data."""

    def mock_responder(_request: InteractionRequest) -> tuple[ResponseChunk, ...]:
        return (ResponseChunk(data=response_data.encode(), sequence=0),)

    data_store.scenario["live_responder"] = mock_responder


@step("Configure tracking live responder returning <response_data>")
def configure_tracking_live_responder(response_data: str) -> None:
    """Configure a live responder that records whether it was called."""
    data_store.scenario["live_responder_called"] = False

    def tracking_responder(_request: InteractionRequest) -> tuple[ResponseChunk, ...]:
        data_store.scenario["live_responder_called"] = True
        return (ResponseChunk(data=response_data.encode(), sequence=0),)

    data_store.scenario["live_responder"] = tracking_responder


@step("Response stream should contain <expected_data>")
def response_stream_should_contain(expected_data: str) -> None:
    """Verify response stream contains expected data."""
    response_chunks = cast(
        "list[ResponseChunk] | None", data_store.scenario.get("response_chunks")
    )
    assert response_chunks is not None, "No response chunks received"
    actual_data = b"".join(chunk.data for chunk in response_chunks)
    assert actual_data == expected_data.encode(), (
        f"Expected {expected_data!r}, got {actual_data!r}"
    )


@step("Cassette should contain one recorded interaction")
def cassette_should_contain_one_interaction() -> None:
    """Verify cassette contains exactly one interaction."""
    cassette = cast("Cassette", data_store.scenario.get("cassette"))
    assert cassette is not None, "No cassette found"
    assert len(cassette.interactions) == 1, (
        f"Expected 1 interaction, got {len(cassette.interactions)}"
    )


@step("Live responder should not be called")
def live_responder_should_not_be_called() -> None:
    """Verify the live responder was not invoked."""
    called = cast("bool", data_store.scenario.get("live_responder_called", False))
    assert called is False, "Expected live responder not to be called"


@step("Live responder should be called")
def live_responder_should_be_called() -> None:
    """Verify the live responder was invoked."""
    called = cast("bool", data_store.scenario.get("live_responder_called", False))
    assert called is True, "Expected live responder to be called"


@step("Serialize and deserialize cassette")
def serialize_and_deserialize_cassette() -> None:
    """Serialize cassette to JSON and deserialize back."""
    cassette = cast("Cassette", data_store.scenario["cassette"])
    json_str = cassette.model_dump_json()
    new_cassette = Cassette.model_validate_json(json_str)
    data_store.scenario["cassette"] = new_cassette


# Persistence functionality steps


@step("Configure JSON file cassette store at temporary path")
def configure_json_file_cassette_store() -> None:
    """Configure a JSON file cassette store at a temporary path."""
    temp_dir = tempfile.TemporaryDirectory()
    path = Path(temp_dir.name) / "cassette.json"
    store = JsonFileCassetteStore(path)
    data_store.scenario["cassette_store"] = store
    data_store.scenario["cassette_store_path"] = path
    data_store.scenario["cassette_store_temp_dir"] = temp_dir


@step("Configure JSON file cassette store with create_if_missing at temporary path")
def configure_json_file_cassette_store_create_if_missing() -> None:
    """Configure a cassette store with create_if_missing at a temporary path."""
    temp_dir = tempfile.TemporaryDirectory()
    path = Path(temp_dir.name) / "cassette.json"
    store = JsonFileCassetteStore(path, create_if_missing=True)
    data_store.scenario["cassette_store"] = store
    data_store.scenario["cassette_store_path"] = path
    data_store.scenario["cassette_store_temp_dir"] = temp_dir


@step("Cassette should have no interactions")
def cassette_should_have_no_interactions() -> None:
    """Verify cassette has no interactions."""
    cassette = cast("Cassette", data_store.scenario["cassette"])
    assert len(cassette.interactions) == 0, (
        f"Expected 0 interactions, got {len(cassette.interactions)}"
    )


@step("Save interaction to cassette for <protocol> <action> <target>")
def save_interaction_to_cassette(protocol: str, action: str, target: str) -> None:
    """Create an interaction and add it to the current cassette."""
    request = InteractionRequest(
        protocol=protocol,
        action=action,
        target=target,
        headers=(),
        body=b"test-data",
    )
    chunks = (ResponseChunk(data=b"response-data", sequence=0),)
    interaction = Interaction(
        request=request,
        fingerprint=request.fingerprint(),
        response_chunks=chunks,
    )
    cassette = cast("Cassette", data_store.scenario["cassette"])
    new_interactions = tuple(cassette.interactions) + (interaction,)
    data_store.scenario["cassette"] = Cassette(interactions=new_interactions)


@step("Save cassette to file store")
def save_cassette_to_file_store() -> None:
    """Save the current cassette to the configured file store."""
    cassette = cast("Cassette", data_store.scenario["cassette"])
    store = cast("JsonFileCassetteStore", data_store.scenario["cassette_store"])
    store.save(cassette)


@step("Storing broker in <mode> mode receives request for <protocol> <action> <target>")
def broker_in_mode_with_store_receives_request(
    mode: str, protocol: str, action: str, target: str
) -> None:
    """Send request to broker with cassette store."""
    cassette = cast("Cassette", data_store.scenario["cassette"])
    live_responder = cast(
        "LiveResponder | None", data_store.scenario.get("live_responder")
    )
    cassette_store = cast(
        "JsonFileCassetteStore", data_store.scenario["cassette_store"]
    )
    try:
        broker = Broker(
            cassette=cassette,
            mode=cast("BrokerMode", mode),
            live_responder=live_responder,
            cassette_store=cassette_store,
        )
        request = InteractionRequest(
            protocol=protocol,
            action=action,
            target=target,
            headers=(),
            body=b"test-data",
        )
        chunks = list(broker.replay(request))
        data_store.scenario["response_chunks"] = chunks
        data_store.scenario["error"] = None
        data_store.scenario["cassette"] = broker.cassette
    except (InteractionNotFoundError, LiveResponderRequiredError) as e:
        data_store.scenario["response_chunks"] = None
        data_store.scenario["error"] = e


@step("Create broker from store in <mode> mode")
def create_broker_from_store(mode: str) -> None:
    """Create a Broker using the from_store factory classmethod."""
    cassette_store = cast(
        "JsonFileCassetteStore", data_store.scenario["cassette_store"]
    )
    live_responder = cast(
        "LiveResponder | None", data_store.scenario.get("live_responder")
    )
    try:
        broker = Broker.from_store(
            cassette_store,
            mode=cast("BrokerMode", mode),
            live_responder=live_responder,
        )
        data_store.scenario["broker"] = broker
        data_store.scenario["error"] = None
    except LiveResponderRequiredError as e:
        data_store.scenario["broker"] = None
        data_store.scenario["error"] = e


@step("Broker replays request for <protocol> <action> <target>")
def broker_replays_request(protocol: str, action: str, target: str) -> None:
    """Replay a request using the broker stored in scenario data."""
    broker = cast("Broker | None", data_store.scenario.get("broker"))
    if broker is None:
        return
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


@step("Cassette file should exist at configured path")
def cassette_file_should_exist() -> None:
    """Verify that the cassette file exists."""
    path = cast("Path", data_store.scenario["cassette_store_path"])
    assert path.exists(), f"Cassette file not found at {path}"


@step("Load cassette from file store")
def load_cassette_from_file_store() -> None:
    """Load cassette from the configured file store."""
    store = cast("JsonFileCassetteStore", data_store.scenario["cassette_store"])
    cassette = store.load()
    data_store.scenario["cassette"] = cassette


@step("Write corrupted JSON to cassette file")
def write_corrupted_json_to_cassette_file() -> None:
    """Write invalid JSON to the cassette file path."""
    path = cast("Path", data_store.scenario["cassette_store_path"])
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("{corrupted json", encoding="utf-8")


@step("Loading cassette from file store should raise CassetteLoadError")
def loading_cassette_should_raise_cassette_load_error() -> None:
    """Verify that loading from file store raises CassetteLoadError."""
    store = cast("JsonFileCassetteStore", data_store.scenario["cassette_store"])
    try:
        store.load()
    except CassetteLoadError as e:
        data_store.scenario["last_cassette_load_error"] = e
        return
    pytest.fail("Expected CassetteLoadError but no error was raised")


@step("The original error should be accessible from CassetteLoadError")
def original_error_should_be_accessible() -> None:
    """Verify that the original cause is accessible via __cause__."""
    error = cast(
        "CassetteLoadError",
        data_store.scenario["last_cassette_load_error"],
    )
    assert error.__cause__ is not None


@after_scenario
def cleanup_cassette_store_tmp() -> None:
    """Clean up temporary cassette store directory after each scenario."""
    temp_dir = cast(
        "tempfile.TemporaryDirectory[str] | None",
        data_store.scenario.get("cassette_store_temp_dir"),
    )
    if temp_dir is None:
        return
    temp_dir.cleanup()
    data_store.scenario.pop("cassette_store_temp_dir", None)
