# ADR 0009: LiveResponder Port for Upstream Forwarding

## Status

Accepted

## Date

2026-01-25

## Context

ADR 0007 introduced broker modes (replay, record, auto). In record and auto modes, when a MISS occurs (no matching interaction in cassette), the Broker must forward the request to a live upstream service and capture the response.

The Broker needs a mechanism to communicate with the upstream, but per ADR 0006 (External Protocol Adapters), the core package must remain protocol-agnostic. The Broker cannot know how to make HTTP calls, database queries, or any protocol-specific operations.

## Decision

Define LiveResponder as a callable port that the user provides.

The signature is: `Callable[[InteractionRequest], Iterable[ResponseChunk]]`

The Broker accepts an optional `live_responder` parameter at construction time.

## Rationale

- **Protocol-agnostic**: The Broker delegates upstream communication to user-provided code. The core library has no protocol dependencies.
- **Simple interface**: A callable is the simplest possible port. No abstract base classes or protocols required.
- **Flexible return type**: `Iterable[ResponseChunk]` supports both simple tuple returns and generator-based streaming.
- **Optional dependency**: `live_responder=None` means no upstream forwarding (pure replay mode behavior).
- **Testable**: Easy to mock in tests with a simple function.
- **Composable**: Multiple responders can be composed into one callable. Lifecycle management (setup/teardown) can be encapsulated in a class with `__call__`.

## Implications

### Positive Implications

- Zero protocol dependencies in core.
- Users have full control over upstream communication.
- Simple to implement for any protocol.
- Natural integration with existing client libraries.

### Concerns

- User must implement responder correctly (mitigation: provide examples, document contract clearly).
- Error handling is user's responsibility (mitigation: document expected behavior, recommend raising exceptions for failures).

## Alternatives

### Abstract Base Class

Define `class LiveResponder(ABC)` with an abstract `respond` method.

- **Pros**: Explicit contract, IDE autocompletion on methods.
- **Cons**: More ceremony, users must subclass instead of just passing a function.
- **Reason for rejection**: Callable is simpler and sufficient. Python's duck typing makes ABC unnecessary.

### Protocol (typing.Protocol)

Define a structural protocol for type checking.

- **Pros**: Type safety without runtime overhead.
- **Cons**: Still more complex than a simple callable type alias.
- **Reason for rejection**: A callable type alias achieves the same goal with less complexity.

## Future Direction

Revisit if:

- Async support is added (consider `AsyncLiveResponder` type).

## References

- ADR 0006: External Protocol Adapters Strategy
- ADR 0007: Broker Mode Parameter for Record Functionality
