# ADR 0013: CassetteStore Load Behavior for Missing Storage

## Status

Accepted

## Date

2026-02-16

## Context

When a CassetteStore implementation attempts to load a cassette, the underlying storage may not yet exist (e.g., a file that has not been created). Different use cases require different behaviors:

1. **Replay-only scenarios**: Missing storage indicates a configuration error and should fail immediately with a clear error
2. **Record/auto scenarios**: Missing storage is expected on first run, and returning an empty cassette allows recording to proceed naturally
3. **Explicit configuration**: The caller should decide the behavior at construction time rather than relying on implicit conventions or runtime flags

## Decision

Store implementations should allow configuring how to handle missing storage at construction time. The default behavior is to raise an error when storage is missing. An opt-in parameter enables returning an empty cassette instead.

This keeps the fail-fast default from ADR-0012 while supporting the legitimate case where storage does not yet exist.

## Rationale

- **Fail-fast by default**: Missing storage is most often a misconfiguration; raising an error prevents silent data loss and debugging confusion
- **Explicit opt-in for lenient behavior**: Callers who expect missing storage must explicitly request empty-cassette behavior, making intent clear in configuration
- **Construction-time configuration**: Binding the behavior at construction avoids per-call ambiguity and ensures consistent behavior throughout the store's lifetime
- **Alignment with recording workflow**: In record and auto modes, the cassette file is created on first save; requiring it to exist before the first load would force unnecessary initialization steps
- **Single responsibility**: The store handles storage concerns (missing vs. present); the caller handles domain concerns (which mode to operate in)

## Implications

### Positive

- Default behavior catches misconfiguration early with clear error messages
- Record workflows can start cleanly without pre-creating empty storage
- Behavior is explicit and visible in construction parameters
- No changes needed to the CassetteStore protocol itself

### Concerns

- Callers must remember to enable lenient behavior for record/auto workflows (mitigation: documentation and examples make this clear, and the error message from the default behavior guides users)
- Two possible behaviors for the same operation may surprise new users (mitigation: the default is the safe choice, and the parameter name communicates intent)

## Alternatives

### Always Raise on Missing Storage

Require storage to exist before any load operation, regardless of configuration.

- **Pros**: Simplest implementation, fully consistent behavior, no ambiguity
- **Cons**: Forces callers to pre-create empty storage files before recording, adds unnecessary setup steps to record workflows
- **Reason for rejection**: Creates friction for the common record/auto use case without meaningful safety benefit

### Always Return Empty Cassette on Missing Storage

Silently return an empty cassette whenever storage is not found.

- **Pros**: Simplest for new users, no configuration needed for record workflows
- **Cons**: Masks misconfiguration errors in replay-only scenarios, violates fail-fast principle from ADR-0012
- **Reason for rejection**: Silent fallback hides bugs; users may not notice they are replaying from an empty cassette due to a typo in the storage path

### Per-Call Parameter on Load Method

Pass a flag to each load() call to control missing-storage behavior.

- **Pros**: Maximum flexibility per invocation
- **Cons**: Inconsistent behavior across calls to the same store, pushes configuration responsibility to every call site, complicates the CassetteStore protocol
- **Reason for rejection**: Construction-time configuration provides consistency and keeps the protocol simple

## Future Direction

If additional storage backends are added, each implementation should follow the same pattern of construction-time configuration for missing-storage behavior.

Consider whether a factory or builder pattern would simplify store construction as the number of configuration options grows.

## References

- [ADR-0011: CassetteStore Persistence Port](0011-cassette-store-persistence-port.md)
- [ADR-0012: Cassette Save Failure Behavior](0012-cassette-save-failure-behavior.md)
