# ADR 0014: Require live_responder for Auto and Record Modes at Construction

## Status

Accepted

## Date

2026-02-25

## Context

`Broker` supports three modes:

1. `replay`: replay from cassette only
2. `record`: always forward to live upstream and record
3. `auto`: replay on HIT, forward-and-record on MISS

Before this decision, `Broker` could be constructed in `auto` (and `record`) mode without `live_responder`. In those cases, errors surfaced later during request handling when forwarding was needed.

This allowed a partially valid runtime configuration and delayed misconfiguration detection. The project prioritizes deterministic testing and fail-fast behavior, so configuration errors should be detected as early as possible.

## Decision

`Broker` must enforce `live_responder` availability at construction time for both `record` and `auto` modes.

- If `mode` is `record` or `auto` and `live_responder` is `None`, raise `LiveResponderRequiredError(mode)` from `Broker.__init__`.
- `Broker.from_store(...)` inherits the same invariant by constructing through `Broker.__init__`.
- `replay` mode continues to allow `live_responder=None`.

## Rationale

- **Fail-fast configuration validation**: invalid mode/responder combinations are rejected immediately.
- **Determinism-first behavior**: avoids hidden runtime branches where missing upstream configuration appears only under specific traffic patterns.
- **Consistent mode contract**: both forwarding-capable modes (`record`, `auto`) require forwarding capability at setup time.
- **Operational clarity**: users preparing `auto` for cassette extension workflows are required to wire upstream explicitly.

## Implications

### Positive Implications

- Misconfiguration is caught at broker creation, not during replay.
- API behavior is stricter and easier to reason about in tests and CI.
- E2E and unit tests can assert configuration validity directly.

### Concerns

- **Breaking change**: existing `auto` usages that relied on replay-only HIT paths without a `live_responder` will fail at initialization (mitigation: document this clearly in release notes and migration guidance, with before/after examples).
- Slightly reduced flexibility for niche `auto` scenarios that never MISS (mitigation: use `replay` mode for pure replay workflows, and reserve `auto` for cache-extend workflows with upstream configured).

## Alternatives

### Keep Existing Deferred Validation

Allow `auto` without `live_responder` and fail only on MISS.

- **Key characteristics**: validation deferred to request handling path.
- **Pros**: supports replay-only HIT flows in `auto` mode.
- **Cons**: weakens fail-fast guarantees and leaves invalid configuration undetected until runtime.
- **Reason for rejection**: conflicts with determinism-first and fail-fast direction.

### Require live_responder for Record Only

Keep `record` strict, leave `auto` deferred.

- **Key characteristics**: mixed validation semantics by mode.
- **Pros**: preserves `auto` flexibility.
- **Cons**: inconsistent validation model across forwarding-capable modes.
- **Reason for rejection**: inconsistent API contracts increase cognitive load and hide misconfiguration.

## Future Direction

- Update release notes to mark this as a breaking change in `0.6.0`.
- Ensure adapter examples and any external integrations configure `live_responder` whenever `auto` or `record` mode is used.
- Revisit this decision only if a non-forwarding variant of `auto` is intentionally introduced as a separate mode with explicit semantics.

## References

- [ADR-0007: Broker Mode Parameter for Record Functionality](0007-broker-mode-parameter.md)
- [ADR-0009: LiveResponder Port for Upstream Forwarding](0009-live-responder-port.md)
- [ADR-0012: Cassette Save Failure Behavior](0012-cassette-save-failure-behavior.md)
