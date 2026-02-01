# ADR 0011: CassetteStore Persistence Port

## Status

Accepted

## Date

2026-01-30

## Context

Record and auto modes update the in-memory Cassette when new interactions are captured. However, there is no persistence mechanism—recorded interactions are lost when the process ends.

Users need a way to persist cassettes automatically, but per ADR 0006 (External Protocol Adapters), the core package must remain storage-agnostic. The Broker cannot assume file I/O, databases, cloud storage, or any specific persistence strategy.

## Decision

Define CassetteStore as a Protocol port with two methods: `load()` and `save()`.

The Broker accepts an optional `cassette_store` parameter at construction time. When configured, the Broker automatically calls `save()` after recording new interactions.

A reference implementation `JsonFileCassetteStore` is provided in a separate module (`stores.py`) to keep JSON/filesystem logic out of core business logic.

## Rationale

- **Protocol over Callable**: Unlike LiveResponder (single method), CassetteStore requires two methods (`load` and `save`). A Protocol provides a clear structural contract.
- **Storage-agnostic**: The Broker delegates persistence to user-provided code. The core library has no I/O dependencies.
- **Auto-save on record**: Automatically persisting after each recording simplifies the common use case. Users don't need to manually save after each interaction.
- **Optional dependency**: `cassette_store=None` means no automatic persistence (current behavior preserved).
- **Separate module for implementation**: `JsonFileCassetteStore` lives in `stores.py`, not `services.py`, keeping JSON serialization details out of the Broker.

## Implications

### Positive Implications

- Zero I/O dependencies in core business logic.
- Users can implement any persistence strategy (files, databases, cloud storage).
- Simple integration—just pass a store to the Broker.
- Automatic saving reduces boilerplate for record/auto workflows.
- Pydantic's built-in serialization makes JSON implementation trivial.

### Concerns

- Synchronous I/O may block during `save()` (mitigation: consider async variant in future).
- Save is called after each recording, which may be expensive for high-frequency recording (mitigation: users can implement buffered/batched stores).
- User must implement store correctly (mitigation: provide JsonFileCassetteStore as reference).

## Alternatives

### Callable for save only

Define `CassetteSaver = Callable[[Cassette], None]` for save-only functionality.

- **Pros**: Simpler, matches LiveResponder pattern.
- **Cons**: No `load()` method, users must manage loading separately.
- **Reason for rejection**: Having both `load()` and `save()` in one interface provides a cohesive persistence abstraction.

### Manual save only

Require users to call `broker.cassette.model_dump_json()` manually.

- **Pros**: No new abstractions needed.
- **Cons**: Error-prone, users may forget to save after recording.
- **Reason for rejection**: Auto-save provides better user experience for the common case.

### Built-in file persistence in Broker

Add file path parameter directly to Broker.

- **Pros**: Simpler API for file-based use case.
- **Cons**: Violates ADR 0006, couples core logic to filesystem.
- **Reason for rejection**: Broker should remain storage-agnostic.

## Future Direction

Revisit if:

- Async support is added (consider `AsyncCassetteStore` Protocol).
- Lifecycle hooks are added (allow validation before save).

## References

- ADR 0006: External Protocol Adapters Strategy
- ADR 0009: LiveResponder Port for Upstream Forwarding
