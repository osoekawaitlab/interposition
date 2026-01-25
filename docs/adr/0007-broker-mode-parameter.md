# ADR 0007: Broker Mode Parameter for Record Functionality

## Status

Accepted

## Date

2026-01-25

## Context

Interposition currently supports only replay mode. The Broker looks up interactions by fingerprint and returns recorded responses. When a MISS occurs, it raises `InteractionNotFoundError`.

To support recording functionality, the Broker needs to handle MISS differently depending on the intended use case:

- **Replay mode**: MISS should raise an error (current behavior).
- **Record mode**: MISS should forward to a live upstream and record the response.
- **Auto mode**: HIT should replay, MISS should forward and record.

The question is how to represent this behavioral variation.

## Decision

Add a `mode` parameter to the Broker class that determines MISS handling behavior.

The mode is set at Broker construction time and remains constant for the lifetime of the Broker instance.

## Rationale

- **Single entry point**: Users interact with one Broker class rather than multiple classes (ReplayBroker, RecordBroker, etc.).
- **Explicit configuration**: The mode is visible in the constructor, making behavior predictable.
- **Backward compatible**: Default mode is "replay", preserving existing behavior.
- **Testable**: Mode can be easily switched in tests without changing other setup.

## Implications

### Positive Implications

- Simple API: `Broker(cassette, mode="auto")`.
- Clear behavioral contract per mode.
- Easy to extend with additional modes if needed.

### Concerns

- Mode validation is static only; runtime validation is not enforced by default (mitigation: rely on type checking and clear documentation).
- Mode affects multiple methods' behavior (mitigation: document clearly, keep logic localized).

## Alternatives

### Separate Classes (ReplayBroker, RecordBroker)

Create distinct classes for each mode.

- **Pros**: Single Responsibility Principle, no conditional logic.
- **Cons**: Code duplication, users must choose correct class, harder to switch modes.
- **Reason for rejection**: The core logic (fingerprinting, cassette lookup) is shared across modes. Separate classes would duplicate this logic.

### Method Parameter

Pass mode to each method call: `broker.handle(request, mode="record")`.

- **Pros**: Flexible per-request behavior.
- **Cons**: Verbose, error-prone, inconsistent behavior within same broker instance.
- **Reason for rejection**: Mode should be a broker-level concern, not a per-request concern.

### Strategy Pattern

Inject a mode strategy object into Broker.

- **Pros**: Extensible, testable strategies.
- **Cons**: Over-engineered for three simple modes, additional abstraction layer.
- **Reason for rejection**: Premature abstraction. A simple parameter suffices for the current requirements.

## Future Direction

Revisit if:

- Modes require significantly different initialization (e.g., different dependencies).
- Per-request mode switching becomes a requirement.
- The number of modes grows beyond what a simple parameter can handle.

## References

- Issue #5: Record mode feature request
