# interposition

Protocol-agnostic interaction interposition with lifecycle hooks for record, replay, and control.

## Overview

Interposition is a Python library for replaying recorded interactions in a protocol-agnostic way. It provides in-memory cassettes that store request-response interactions and a broker that replays matching responses based on request fingerprints.

**Key Features:**

- **Protocol-agnostic**: Works with any protocol (HTTP, gRPC, database calls, etc.)
- **Type-safe**: Full mypy strict mode support with Pydantic v2
- **Immutable**: All data structures are frozen Pydantic models
- **Serializable**: Built-in JSON/YAML serialization for cassette persistence
- **Memory-efficient**: O(1) lookup with fingerprint indexing
- **Streaming**: Generator-based response delivery

## Installation

```bash
# Development installation
pip install -e .
```

## Quick Start

```python
from interposition import (
    Broker,
    Cassette,
    Interaction,
    InteractionRequest,
    ResponseChunk,
)

# Create a request
request = InteractionRequest(
    protocol="test-proto",
    action="fetch",
    target="resource-123",
    headers=(("X-Custom-Header", "value"),),
    body=b'{"key": "value"}',
)

# Create response chunks
chunks = (
    ResponseChunk(data=b"response-part1", sequence=0),
    ResponseChunk(data=b"response-part2", sequence=1),
)

# Create an interaction (recorded request-response pair)
interaction = Interaction(
    request=request,
    fingerprint=request.fingerprint(),
    response_chunks=chunks,
)

# Create a cassette with recorded interactions
cassette = Cassette(interactions=(interaction,))

# Create a broker for replay
broker = Broker(cassette=cassette)

# Replay the response for a matching request
for chunk in broker.replay(request):
    print(f"Chunk {chunk.sequence}: {chunk.data}")
# Output:
# Chunk 0: b'response-part1'
# Chunk 1: b'response-part2'
```

## Usage Examples

### Basic Replay

```python
from interposition import (
    Broker,
    Cassette,
    Interaction,
    InteractionRequest,
    ResponseChunk,
)

# Record an interaction
request = InteractionRequest(
    protocol="api",
    action="query",
    target="users/42",
    headers=(),
    body=b"",
)

response = (
    ResponseChunk(data=b'{"id": 42, "name": "Alice"}', sequence=0),
)

interaction = Interaction(
    request=request,
    fingerprint=request.fingerprint(),
    response_chunks=response,
)

# Create cassette and broker
cassette = Cassette(interactions=(interaction,))
broker = Broker(cassette=cassette)

# Replay
chunks = list(broker.replay(request))
assert len(chunks) == 1
assert chunks[0].data == b'{"id": 42, "name": "Alice"}'
```

### Handling Missing Interactions

```python
from interposition import Broker, InteractionNotFoundError, InteractionRequest

# Attempt to replay an unrecorded request
different_request = InteractionRequest(
    protocol="api",
    action="query",
    target="users/99",  # Different target
    headers=(),
    body=b"",
)

try:
    list(broker.replay(different_request))
except InteractionNotFoundError as e:
    print(f"No matching interaction found for: {e.request.target}")
    # Output: No matching interaction found for: users/99
```

### Multi-Chunk Streaming

```python
# Large response split into multiple chunks
large_response = (
    ResponseChunk(data=b"chunk-1" * 1000, sequence=0),
    ResponseChunk(data=b"chunk-2" * 1000, sequence=1),
    ResponseChunk(data=b"chunk-3" * 1000, sequence=2),
)

interaction = Interaction(
    request=request,
    fingerprint=request.fingerprint(),
    response_chunks=large_response,
)

cassette = Cassette(interactions=(interaction,))
broker = Broker(cassette=cassette)

# Process chunks incrementally
for chunk in broker.replay(request):
    # Process each chunk as it arrives (streaming)
    process_chunk(chunk.data)
```

### Multiple Interactions in Cassette

```python
# Create multiple interactions
interactions = []

for i in range(10):
    req = InteractionRequest(
        protocol="api",
        action="fetch",
        target=f"resource-{i}",
        headers=(),
        body=b"",
    )
    resp = (ResponseChunk(data=f"data-{i}".encode(), sequence=0),)
    interaction = Interaction(
        request=req,
        fingerprint=req.fingerprint(),
        response_chunks=resp,
    )
    interactions.append(interaction)

# Create cassette with all interactions
cassette = Cassette(interactions=tuple(interactions))
broker = Broker(cassette=cassette)

# Replay any recorded request (O(1) lookup)
request_5 = InteractionRequest(
    protocol="api",
    action="fetch",
    target="resource-5",
    headers=(),
    body=b"",
)
chunks = list(broker.replay(request_5))
assert chunks[0].data == b"data-5"
```

### Request Fingerprinting

```python
# Requests with identical content produce identical fingerprints
request1 = InteractionRequest(
    protocol="api",
    action="get",
    target="users",
    headers=(("Accept", "application/json"),),
    body=b"",
)

request2 = InteractionRequest(
    protocol="api",
    action="get",
    target="users",
    headers=(("Accept", "application/json"),),
    body=b"",
)

assert request1.fingerprint() == request2.fingerprint()

# Header order doesn't matter (canonical ordering)
request3 = InteractionRequest(
    protocol="api",
    action="get",
    target="users",
    headers=(("Accept", "application/json"), ("User-Agent", "test")),
    body=b"",
)

request4 = InteractionRequest(
    protocol="api",
    action="get",
    target="users",
    headers=(("User-Agent", "test"), ("Accept", "application/json")),
    body=b"",
)

assert request3.fingerprint() == request4.fingerprint()
```

### Cassette Serialization

```python
import json

# Save cassette to JSON file
cassette = Cassette(interactions=(interaction,))
json_data = cassette.model_dump_json(indent=2)

with open("cassette.json", "w") as f:
    f.write(json_data)

# Load cassette from JSON file
with open("cassette.json") as f:
    loaded_cassette = Cassette.model_validate_json(f.read())

# Verify loaded cassette works
broker = Broker(cassette=loaded_cassette)
chunks = list(broker.replay(request))
assert chunks[0].data == b'{"id": 42, "name": "Alice"}'
```

### Python Dict Serialization

```python
# Serialize to Python dict
cassette_dict = cassette.model_dump()
print(cassette_dict)
# {'interactions': [{'request': {...}, 'fingerprint': {...}, ...}]}

# Deserialize from Python dict
restored_cassette = Cassette.model_validate(cassette_dict)
```

### JSON Schema Generation

```python
# Generate JSON schema for documentation
schema = Cassette.model_json_schema()
print(json.dumps(schema, indent=2))
# {
#   "type": "object",
#   "properties": {
#     "interactions": {...}
#   },
#   ...
# }
```

## API Documentation

### Core Classes

- **`InteractionRequest`**: Immutable request data (protocol, action, target, headers, body)
- **`RequestFingerprint`**: SHA-256 hash-based request identifier
- **`ResponseChunk`**: Single chunk of response data with sequence number
- **`Interaction`**: Recorded request-response pair with fingerprint
- **`Cassette`**: Immutable collection of interactions with O(1) fingerprint index
- **`Broker`**: Replay engine that matches requests and streams responses

### Exceptions

- **`InteractionNotFoundError`**: Raised when no matching interaction exists for a request
- **`InteractionValidationError`**: Raised when interaction validation fails (e.g., fingerprint mismatch, invalid chunk sequence)

## Development

### Prerequisites

- Python 3.10+
- [uv](https://github.com/astral-sh/uv) (recommended) or pip

### Setup

```bash
# Clone repository
git clone https://github.com/osoekawaitlab/interposition.git
cd interposition

# Install dependencies
uv pip install -e . --group=dev
```

### Running Tests

```bash
# Run all tests
nox -s tests

# Run unit tests only
nox -s tests_unit

# Run E2E tests only
nox -s tests_e2e

# Run all test sessions (all Python versions)
nox -s tests_all_versions
```

### Code Quality

```bash
# Type checking
nox -s mypy

# Linting
nox -s lint

# Format code
nox -s format_code
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
