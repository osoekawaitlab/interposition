# ADR 0005: Build Fingerprint Index for O(1) Lookup

## Status

Accepted

## Date

2026-01-05

## Context

The cassette stores interactions as a tuple and needs to find interactions matching a given request fingerprint. Without an index, finding a match requires linear search (O(n)) through all interactions. For large cassettes with hundreds or thousands of interactions, this becomes a performance bottleneck.

## Decision

Build a `dict[RequestFingerprint, int]` index at cassette construction that maps fingerprints to their first occurrence position in the interactions tuple. The index is built using a model validator and stored as a private attribute.

## Rationale

- **O(1) lookup**: Dictionary lookup is constant time, vastly superior to O(n) linear search
- **Initialization cost**: Index is built once during cassette creation, amortized over many lookups
- **Memory efficiency**: Index stores only integers (positions), not duplicate interaction data
- **First-match alignment**: Index naturally stores first occurrence, implementing ADR 0004
- **Immutable after creation**: Index is built during construction and never modified
- **Transparent**: Implementation detail hidden from users (private attribute)

## Implications

### Positive Implications

- Replay performance is independent of cassette size (O(1) vs O(n))
- Enables large cassettes (thousands of interactions) without performance degradation
- Simple implementation using standard library dict
- Index construction is deterministic and testable
- Memory overhead is minimal (one int per unique fingerprint)

### Concerns

- Upfront cost to build index during cassette creation (mitigation: acceptable one-time cost amortized over many lookups)
- Uses `object.__setattr__` to mutate frozen model (mitigation: required for immutability, Pydantic pattern for private attributes)
- Memory overhead for the index dict (mitigation: minimal, ~8 bytes per unique fingerprint)
- Index is not exposed in serialization or repr (mitigation: intentional design, private implementation detail)

## Alternatives

### Linear Search (No Index)

Finding interactions by iterating through the tuple without an index.

- **Pros**: No memory overhead, simpler implementation
- **Cons**: O(n) lookup time becomes bottleneck for large cassettes, performance degrades proportionally with cassette size
- **Reason for rejection**: Performance is unacceptable for production use with large cassettes (hundreds or thousands of interactions)

### Build Index on First Lookup (Lazy Initialization)

Deferring index construction until the first lookup call.

- **Pros**: Defers cost if cassette is never used
- **Cons**: Requires mutable state to track "index built" flag, violates frozen model immutability principle
- **Reason for rejection**: Breaks immutability guarantees; construction-time indexing is simpler and aligns with frozen model design

### External Index (Separate Data Structure)

Maintaining the index as a separate object outside the cassette.

- **Pros**: Clear separation of concerns
- **Cons**: Requires managing two objects (cassette + index) in sync, more complex API (users must pass both), risk of desynchronization if index is mutated
- **Reason for rejection**: API complexity and synchronization risk outweigh benefits; internal index is simpler and safer

### Use List Instead of Tuple for Interactions

Storing interactions in a mutable list to enable direct mutation.

- **Pros**: No workaround needed for frozen models
- **Cons**: Mutable collection contradicts immutability principle, no advantage for index-based access (tuple supports indexing)
- **Reason for rejection**: Immutability is a core design principle; tuple is the correct choice for frozen data

### Store Interactions in Dict (No Tuple)

Using a dict mapping fingerprints to interactions directly, eliminating the tuple.

- **Pros**: Built-in O(1) lookup without separate index
- **Cons**: Loses insertion order for duplicates (violates ADR 0004), cannot represent multiple interactions with same fingerprint, fundamentally different data model
- **Reason for rejection**: Incompatible with first-match strategy; duplicates are legitimate and must be preserved in order

## Future Direction

This decision should be revisited if:

- Profiling shows index build time is a bottleneck (unlikely, dict insert is fast)
- Memory pressure from large indexes becomes an issue (consider specialized data structures)
- Alternative frozen dataclass patterns emerge (Python 3.13+ features)
- Cassette persistence requires serializing/deserializing the index (versioning strategy needed)

## References

- [Python dict implementation](https://docs.python.org/3/library/stdtypes.html#dict)
- [Dataclass frozen=True documentation](https://docs.python.org/3/library/dataclasses.html#frozen-instances)
- [Big-O Complexity of Python Operations](https://wiki.python.org/moin/TimeComplexity)
