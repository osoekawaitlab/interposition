# ADR 0003: Use Generator Pattern for Response Streaming

## Status

Accepted

## Date

2026-01-05

## Context

The replay system needs to deliver response chunks to consumers. Responses may consist of multiple chunks that should be delivered in sequence. The library must support both small responses (single chunk) and potentially large responses (many chunks) without excessive memory usage.

## Decision

Use Python generators (`Iterator[ResponseChunk]`) for streaming response chunks. The `Broker.replay()` method returns an iterator that yields chunks lazily.

## Rationale

- **Memory efficiency**: Chunks are yielded one at a time, avoiding loading entire response into memory
- **Lazy evaluation**: Consumers can process chunks as they arrive, enabling streaming workflows
- **Pythonic**: Generator pattern is idiomatic Python for sequential data
- **Composable**: Generators can be chained, filtered, or transformed using standard itertools
- **Backpressure**: Consumer controls iteration pace, natural flow control
- **Testable**: Easy to collect into list for testing (`list(broker.replay(request))`)

## Implications

### Positive Implications

- Scales to arbitrarily large responses without memory pressure
- Natural fit for streaming protocols (HTTP chunked encoding, gRPC streaming, etc.)
- Consumers can process chunks incrementally (progress indicators, real-time processing)
- Simple implementation using `yield from interaction.response_chunks`
- Clear iteration boundary (StopIteration signals completion)

### Concerns

- Consumers must iterate to completion with no random access to middle chunks (mitigation: acceptable tradeoff for memory efficiency)
- Generator state cannot be reset for re-iteration (mitigation: call `replay()` again to get new generator)
- Error handling requires try/except around iteration, not just the initial call (mitigation: standard Python pattern for iterators)
- Some consumers may prefer materialized list (mitigation: use `list()` wrapper when needed)

## Alternatives

### Return Tuple of Chunks

Returning all chunks as a tuple immediately.

- **Pros**: Simpler for consumers that need all chunks upfront, immutable collection
- **Cons**: Entire response must be loaded into memory before returning, no memory savings for large responses
- **Reason for rejection**: Defeats purpose of streaming; memory inefficient for large responses

### Return List of Chunks

Returning all chunks as a list immediately.

- **Pros**: Familiar collection type, random access support
- **Cons**: Same memory concerns as tuple, mutable return type contradicts immutability principle
- **Reason for rejection**: Memory inefficiency plus mutability concerns

### Async Generator (`AsyncIterator[ResponseChunk]`)

Using async generators for streaming chunks.

- **Pros**: Natural fit for I/O-bound operations, enables concurrent processing
- **Cons**: Adds complexity without clear benefit for in-memory replay, forces async/await on all consumers
- **Reason for rejection**: Unnecessary complexity for in-memory cassettes; consider for future I/O-based backends

### Callback-based API

Using callback functions to deliver chunks (e.g., `replay(request, on_chunk=callback)`).

- **Pros**: Familiar pattern from JavaScript, enables push-based flow
- **Cons**: Less Pythonic, harder to compose, inverted control flow is harder to test, no natural backpressure mechanism
- **Reason for rejection**: Generators provide better ergonomics and testability in Python

## Future Direction

This decision should be revisited if:

- Async I/O support is added (consider `AsyncIterator[ResponseChunk]`)
- Profiling shows generator overhead is measurable (unlikely)
- Random access to chunks is frequently needed (consider hybrid approach with optional materialization)

## References

- [PEP 255 - Simple Generators](https://peps.python.org/pep-0255/)
- [Python Iterator Protocol](https://docs.python.org/3/library/stdtypes.html#iterator-types)
