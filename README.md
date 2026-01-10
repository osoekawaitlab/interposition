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

### Error Handling

If a matching interaction is not found, the broker raises `InteractionNotFoundError`:

```python
from interposition import InteractionNotFoundError

try:
    broker.replay(unknown_request)
except InteractionNotFoundError as e:
    print(f"Not recorded: {e.request.target}")
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

## Architecture

See [Architecture Decision Records](docs/architecture/adr.md) for details on design decisions:

- [ADR 0001: Pydantic v2 for Data Models](docs/adr/0001-pydantic-for-data-models.md)
- [ADR 0002: SHA-256 Fingerprinting](docs/adr/0002-sha256-fingerprinting.md)
- [ADR 0003: Generator Streaming](docs/adr/0003-generator-streaming.md)
- [ADR 0004: First-Match Strategy](docs/adr/0004-first-match-strategy.md)
- [ADR 0005: Cassette Index](docs/adr/0005-cassette-index.md)

## License

MIT