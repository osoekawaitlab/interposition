# ADR 0010: Buffer Live Responses Before Recording

## Status

Accepted

## Date

2026-01-25

## Context

Record/auto modes forward a MISS to a live responder and capture the response as an Interaction. The Broker previously streamed chunks as they arrived and recorded only after the consumer finished iterating.

This behavior makes recording fragile: if the consumer stops early, the recording never completes and the cassette is left unchanged.

## Decision

In record/auto mode on a MISS, fully collect the live response chunks before returning any data to the caller. After the full response is collected:

1. Create the Interaction
2. Append it to the cassette
3. Yield the collected chunks

## Rationale

- **Recording integrity**: The cassette is updated even if the consumer stops early.
- **Determinism**: Recording completes before any response is exposed.
- **Validation**: Interaction validation can run before the response is returned.

## Implications

### Positive Implications

- Reliable recording regardless of consumer behavior.
- Consistent cassette state after each replay call.
- Clearer error timing (validation failures occur before any data is returned).

### Concerns

- Increased memory usage for large responses (mitigation: limit record mode to test fixtures or add size caps in a future policy).
- Additional latency before the first byte is returned in record/auto mode (mitigation: acceptable for record mode; replay mode remains streaming).
- Record path is no longer truly streaming (mitigation: introduce an opt-in streaming record path later if needed).

## Alternatives

### Stream Then Record

Yield chunks as they arrive and record after iteration completes.

- **Pros**: Minimal memory use, true streaming.
- **Cons**: Recording fails if the consumer stops early.
- **Reason for rejection**: Violates the requirement that recording should complete even when the consumer cancels early.

### Tee Stream With Background Recording

Yield chunks immediately while a background task consumes and records the full stream.

- **Pros**: Streaming behavior with reliable recording.
- **Cons**: More complexity (threading/async), harder error handling, unclear lifecycle semantics.
- **Reason for rejection**: Too complex for v0; adds concurrency concerns to the core.

### Partial Recording

Persist only the chunks that were consumed by the caller.

- **Pros**: Keeps streaming, avoids buffering.
- **Cons**: Produces incomplete interactions, undermines replay determinism.
- **Reason for rejection**: Incomplete recordings are not acceptable for deterministic replay.

## Future Direction

Revisit if:

- Large responses cause unacceptable memory pressure.
- Async APIs are introduced and background recording becomes feasible.
- A record policy needs to allow streaming with explicit "best effort" semantics.

## References

- ADR 0007: Broker Mode Parameter for Record Functionality
- ADR 0009: LiveResponder Port for Upstream Forwarding
