# ADR 0012: Cassette Save Failure Behavior

## Status

Accepted

## Date

2026-01-31

## Context

In record or auto mode, the Broker can be configured with a `CassetteStore` to persist newly recorded interactions. Save operations may fail due to I/O errors (permissions, disk full, etc.). The Broker must define how to behave when persistence fails while handling a request.

The library's primary motivation is to stabilize nondeterministic API behavior for repeatable tests. If a recorded interaction cannot be persisted, future replays cannot rely on it.

## Decision

If saving a cassette fails, the error is propagated to the caller and the response stream does not continue. This is a fail-fast behavior.

## Rationale

- **Reproducibility-first**: A request that cannot be persisted undermines the core testing goal. Failing the current run surfaces the issue immediately.
- **Consistency with evaluation**: Users may evaluate responses and fail tests based on content; persistence failure is treated as an equally fatal error.
- **Visibility**: Suppressing persistence errors could hide issues and create false confidence in test stability.

## Implications

### Positive Implications

- Persistence failures are immediately visible.
- Test runs remain honest about what is actually reproducible.

### Concerns

- Saves are synchronous; transient I/O failures will fail the request (mitigation: implement a retrying or buffered CassetteStore).
- Users who want "best-effort persistence" must implement a custom store that　swallows or defers errors (mitigation: provide a documented example store if　demand emerges).

## Alternatives

### Best-effort save (log and continue)

- **Pros**: Response always delivered.
- **Cons**: Failures can be hidden, undermining reproducibility.
- **Reason for rejection**: Conflicts with the primary testing motivation.

### Configurable save failure policy

- **Pros**: Flexible for different use cases.
- **Cons**: Adds complexity and policy surface area.
- **Reason for deferral**: Not needed for current scope; can be revisited if demand emerges.

## Future Direction

Revisit if:

- Users request configurable save-failure policies (e.g., warn-and-continue).
- An async broker is introduced and persistence behavior changes.
- The project adds standardized store adapters beyond the JSON file reference.

## References

- ADR 0011: CassetteStore Persistence Port
