# interposition

Protocol-agnostic interaction interposition with lifecycle hooks for record, replay, and control.

## Overview

Interposition is a Python library for replaying recorded interactions. Unlike VCRpy or other HTTP-specific tools, **Interposition does not automatically hook into network libraries**.

Instead, it provides a **pure logic engine** for storage, matching, and replay. You write the adapter for your specific target (HTTP client, database driver, IoT message handler), and Interposition handles the rest.

**Key Features:**

- **Protocol-agnostic**: Works with any protocol (HTTP, gRPC, SQL, Pub/Sub, etc.)
- **Type-safe**: Full mypy strict mode support with Pydantic v2
- **Immutable**: All data structures are frozen Pydantic models
- **Serializable**: Built-in JSON/YAML serialization for cassette persistence
- **Memory-efficient**: O(1) lookup with fingerprint indexing
- **Streaming**: Generator-based response delivery
- **Multi-mode**: Supports replay, record, and auto modes

## Architecture

Interposition sits behind your application's data access layer. You provide the "Adapter" that captures live traffic or requests replay from the Broker.

```text
+-------------+      +------------------+      +---------------+
| Application | <--> | Your Adapter     | <--> | Interposition |
+-------------+      +------------------+      +---------------+
                            |                          |
                       (Traps calls)              (Manages)
                                                       |
                                                  [Cassette]
```

## Installation

```bash
pip install interposition
```

## Practical Integration (Pytest Recipe)

The most common use case is using Interposition as a test fixture. Here is a production-ready recipe for `pytest`:

```python
import pytest
from interposition import Broker, Cassette, InteractionRequest

@pytest.fixture
def cassette_broker():
    # Load cassette from a JSON file (or create one programmatically)
    with open("tests/fixtures/my_cassette.json", "rb") as f:
        cassette = Cassette.model_validate_json(f.read())
    return Broker(cassette)

def test_user_service(cassette_broker, monkeypatch):
    # 1. Create your adapter (mocking your actual client)
    def mock_fetch(url):
        request = InteractionRequest(
            protocol="http",
            action="GET",
            target=url,
            headers=(),
            body=b"",
        )
        # Delegate to Interposition
        chunks = list(cassette_broker.replay(request))
        return chunks[0].data

    # 2. Inject the adapter
    monkeypatch.setattr("my_app.client.fetch", mock_fetch)

    # 3. Run your test
    from my_app import get_user_name
    assert get_user_name(42) == "Alice"
```

## Protocol-Agnostic Examples

Interposition shines where HTTP-only tools fail.

### SQL Database Query

```python
request = InteractionRequest(
    protocol="postgres",
    action="SELECT",
    target="users_table",
    headers=(),
    body=b"SELECT id, name FROM users WHERE id = 42",
)
# Replay returns: b'[(42, "Alice")]'
```

### MQTT / PubSub Message

```python
request = InteractionRequest(
    protocol="mqtt",
    action="subscribe",
    target="sensors/temp/room1",
    headers=(("qos", "1"),),
    body=b"",
)
# Replay returns stream of messages: b'24.5', b'24.6', ...
```

## Usage Guide

### Manual Construction (Quick Start)

If you need to build interactions programmatically (e.g., for seeding tests):

```python
from interposition import (
    Broker,
    Cassette,
    Interaction,
    InteractionRequest,
    ResponseChunk,
)

# 1. Define the Request
request = InteractionRequest(
    protocol="api",
    action="query",
    target="users/42",
    headers=(),
    body=b"",
)

# 2. Define the Response
chunks = (
    ResponseChunk(data=b'{"id": 42, "name": "Alice"}', sequence=0),
)

# 3. Create Interaction & Cassette
interaction = Interaction(
    request=request,
    fingerprint=request.fingerprint(),
    response_chunks=chunks,
)
cassette = Cassette(interactions=(interaction,))

# 4. Replay
broker = Broker(cassette=cassette)
response = list(broker.replay(request))
```

### Persistence & Serialization

Interposition models are Pydantic v2 models, making serialization trivial.

```python
# Save to JSON
with open("cassette.json", "w") as f:
    f.write(cassette.model_dump_json(indent=2))

# Load from JSON
with open("cassette.json") as f:
    cassette = Cassette.model_validate_json(f.read())

# Generate JSON Schema
schema = Cassette.model_json_schema()
```

### Streaming Responses

For large files or streaming protocols, responses are yielded lazily:

```python
# The broker returns a generator
for chunk in broker.replay(request):
    print(f"Received chunk: {len(chunk.data)} bytes")
```

### Broker Modes

The `Broker` supports three modes via the `mode` parameter:

| Mode | Behavior |
|------|----------|
| `replay` | Default. Returns recorded responses only. Raises `InteractionNotFoundError` on cache miss. |
| `record` | Always forwards to live responder and records. Ignores existing cassette entries. |
| `auto` | Returns recorded response if available; otherwise forwards to live and records. |

The `BrokerMode` type alias is available for type hints:

```python
from interposition import BrokerMode

mode: BrokerMode = "auto"
```

### Live Responder

For `record` and `auto` modes, you must provide a `live_responder` callable that forwards requests to your actual backend:

```python
from interposition import (
    Broker,
    Cassette,
    InteractionRequest,
    ResponseChunk,
)
from collections.abc import Iterable

def my_live_responder(request: InteractionRequest) -> Iterable[ResponseChunk]:
    """Forward request to actual backend and yield response chunks."""
    # Your actual implementation here
    response = your_http_client.request(
        method=request.action,
        url=request.target,
        headers=dict(request.headers),
        data=request.body,
    )
    yield ResponseChunk(data=response.content, sequence=0)
```

The `LiveResponder` type alias is available:

```python
from interposition.services import LiveResponder
```

### Record Mode

Use `record` mode to capture new interactions:

```python
# Start with empty cassette
cassette = Cassette(interactions=())

broker = Broker(
    cassette=cassette,
    mode="record",
    live_responder=my_live_responder,
)

# All requests are forwarded and recorded
response = list(broker.replay(request))

# Save the updated cassette
with open("cassette.json", "w") as f:
    f.write(broker.cassette.model_dump_json(indent=2))
```

### Auto Mode

Use `auto` mode for hybrid workflows (replay if available, record if not):

```python
# Load existing cassette (may be empty or partial)
with open("cassette.json") as f:
    cassette = Cassette.model_validate_json(f.read())

broker = Broker(
    cassette=cassette,
    mode="auto",
    live_responder=my_live_responder,
)

# Returns recorded response if exists, otherwise forwards and records
response = list(broker.replay(request))
```

### Cassette Store

For automatic cassette persistence during recording, use a `CassetteStore`. The `CassetteStore` protocol defines a simple interface for loading and saving cassettes:

```python
from interposition import CassetteStore

class MyCassetteStore:
    """Custom store implementation."""

    def load(self) -> Cassette:
        """Load cassette from storage."""
        ...

    def save(self, cassette: Cassette) -> None:
        """Save cassette to storage."""
        ...
```

When a `cassette_store` is provided to the `Broker`, it automatically saves the cassette after each recorded interaction.

### JsonFileCassetteStore

A built-in file-based cassette store using JSON format:

```python
from pathlib import Path
from interposition import Broker, Cassette, JsonFileCassetteStore

# Create store pointing to a JSON file
store = JsonFileCassetteStore(Path("cassettes/my_test.json"))

# Load existing cassette (raises FileNotFoundError if not exists)
cassette = store.load()

# Or start with empty cassette
cassette = Cassette(interactions=())

# Create broker with automatic persistence
broker = Broker(
    cassette=cassette,
    mode="record",
    live_responder=my_live_responder,
    cassette_store=store,  # Auto-saves after each recording
)

# After replay, cassette is automatically saved to file
response = list(broker.replay(request))
```

The `JsonFileCassetteStore` creates parent directories automatically when saving.

### Error Handling

All interposition exceptions inherit from `InterpositionError`, allowing you to catch all domain errors with a single handler:

```python
from interposition import InterpositionError

try:
    broker.replay(request)
except InterpositionError as e:
    print(f"Interposition error: {e}")
```

**InteractionNotFoundError**: Raised when no matching interaction exists (in `replay` mode) or when `auto` mode has a cache miss without a configured `live_responder`:

```python
from interposition import InteractionNotFoundError

try:
    broker.replay(unknown_request)
except InteractionNotFoundError as e:
    print(f"Not recorded: {e.request.target}")
```

**LiveResponderRequiredError**: Raised when `record` mode is used without a `live_responder`:

```python
from interposition import LiveResponderRequiredError

broker = Broker(cassette=cassette, mode="record")  # No live_responder!

try:
    broker.replay(request)
except LiveResponderRequiredError as e:
    print(f"live_responder required for {e.mode} mode")
```

**InteractionValidationError**: Raised when an `Interaction` fails validation (e.g., fingerprint mismatch or invalid response chunk sequence):

```python
from interposition import Interaction, InteractionValidationError

try:
    # This will fail: fingerprint doesn't match request
    interaction = Interaction(
        request=request,
        fingerprint=wrong_fingerprint,  # Mismatch!
        response_chunks=chunks,
    )
except InteractionValidationError as e:
    print(f"Validation failed: {e}")
```

**CassetteSaveError**: Raised when `JsonFileCassetteStore.save()` fails due to I/O errors (permission denied, disk full, etc.):

```python
from pathlib import Path
from interposition import CassetteSaveError, JsonFileCassetteStore

store = JsonFileCassetteStore(Path("/readonly/cassette.json"))

try:
    store.save(cassette)
except CassetteSaveError as e:
    print(f"Failed to save to {e.path}: {e.__cause__}")
```

## Version

Access the package version programmatically:

```python
from interposition import __version__

print(__version__)  # e.g., "0.2.0"
```

## Development

### Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (recommended)

### Setup & Testing

```bash
# Clone and install
git clone https://github.com/osoekawaitlab/interposition.git
cd interposition
uv pip install -e . --group=dev

# Run tests
nox -s tests
```

## License

MIT
