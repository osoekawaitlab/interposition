# ADR 0004: Use First-Match Strategy for Duplicate Interactions

## Status

Accepted

## Date

2026-01-05

## Context

A cassette may contain multiple interactions with identical request fingerprints (same protocol, action, target, headers, and body) but different responses. This can occur when recording non-deterministic endpoints or capturing time-series data. The replay system must define which interaction to return when multiple matches exist.

## Decision

Always return the **first** matching interaction when multiple interactions share the same fingerprint. Subsequent matches are ignored during replay.

## Rationale

- **Determinism**: First-match guarantees consistent behavior across replay sessions
- **Simplicity**: No complex selection logic or state tracking required
- **Testability**: Easy to verify behavior with duplicate interactions
- **Predictability**: Insertion order (recording order) determines replay order
- **O(1) performance**: First-match enables simple index-based lookup (see ADR 0005)
- **Clear semantics**: "First recorded, first replayed" is intuitive

## Implications

### Positive Implications

- Deterministic replay behavior simplifies debugging
- Implementation is trivial (index stores first occurrence)
- No need for match counters or stateful replay logic
- Clear contract: cassette creation order matters
- Works naturally with append-only recording workflows

### Concerns

- Subsequent duplicate interactions are silently ignored (mitigation: intentional design for simplicity; users can filter cassettes if needed)
- No built-in support for stateful replay sequences (mitigation: can be layered on top with StatefulBroker wrapper in future)
- Users cannot specify which duplicate to use without cassette manipulation (mitigation: cassette ordering is under user control)
- Order dependency may surprise users expecting round-robin or random selection (mitigation: documented behavior; first-match is intuitive)

## Alternatives

### All-Match (Return Iterator of All Matches)

Returning an iterator of all matching interactions instead of a single match.

- **Pros**: Preserves all recorded data
- **Cons**: Unclear which response to use for a single replay, forces complexity onto consumers
- **Reason for rejection**: Does not solve the fundamental question of which response to use; pushes decision-making burden onto every consumer

### Round-Robin Strategy

Cycling through matching interactions on successive calls.

- **Pros**: Could model stateful interactions
- **Cons**: Requires mutable state in Broker (violates immutability principle), non-deterministic across different broker instances
- **Reason for rejection**: Breaks immutability guarantees and makes replay behavior unpredictable when using multiple broker instances

### Random Selection

Randomly selecting one of the matching interactions.

- **Pros**: Simple to implement
- **Cons**: Non-deterministic makes testing harder, no clear use case for this behavior, violates principle of predictable replay
- **Reason for rejection**: Non-determinism is fundamentally incompatible with the goal of reproducible test fixtures

### Raise Error on Duplicates

Throwing an error when duplicate fingerprints are detected in a cassette.

- **Pros**: Makes order dependency explicit
- **Cons**: Too strict, prevents legitimate recording scenarios, forces users to deduplicate cassettes manually
- **Reason for rejection**: Overly restrictive; duplicates are legitimate in real-world recording (non-deterministic endpoints, time-series data)

### Last-Match Strategy

Returning the last matching interaction instead of the first.

- **Pros**: Simple to implement
- **Cons**: Counter-intuitive (why record earlier interactions if they're ignored?), no advantage over first-match
- **Reason for rejection**: No meaningful benefit over first-match while being less intuitive about why earlier recordings exist

## Future Direction

This decision should be revisited if:

- Stateful replay (consuming interactions on use) is needed (add explicit mode or new Broker type)
- Users frequently need round-robin behavior (consider StatefulBroker wrapper)
- Duplicate detection is required (add validation utility, not core behavior)
- Complex matching strategies are needed (introduce pluggable strategy pattern)
- Matching strategy becomes pluggable (keep first-match as the default when duplicates occur)

Use first-match as the foundation. More complex strategies can be layered on top without changing the core behavior.

## References

- VCR.rb uses first-match by default for duplicate cassettes
- WireMock uses priority-based matching (more complex, rejected for v0)
