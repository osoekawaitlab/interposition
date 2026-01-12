# ADR 0001: Use Pydantic v2 for Data Models

## Status

Accepted

## Date

2026-01-05

## Context

Interposition's data models (ResponseChunk, InteractionRequest, RequestFingerprint, Interaction, Cassette) are immutable structures representing recorded interactions. The library needs:

1. **Serialization**: Save/load cassettes to/from JSON files for persistence
2. **Runtime Validation**: Validate data when loading cassettes from external sources
3. **Immutability**: Prevent accidental modification of recorded data

## Decision

Use Pydantic v2 `BaseModel` with `ConfigDict(frozen=True)` for all data models.

Domain services (e.g., Broker) use regular Python classes since they don't require serialization.

## Rationale

- **Built-in Serialization**: `model_dump_json()` and `model_validate_json()` eliminate need for custom serialization code
- **Automatic Validation**: Validates data at construction and deserialization, catching malformed cassette files
- **Immutability**: `ConfigDict(frozen=True)` provides same guarantees as frozen dataclasses
- **Type Safety**: Excellent mypy strict mode support via pydantic.mypy plugin
- **Performance**: Rust core makes validation overhead negligible
- **Clean Validation API**: `@model_validator` for cross-field validation (e.g., fingerprint matching)

## Implications

### Positive

- Cassette persistence without custom code
- Automatic validation catches corrupted files
- JSON schema generation for documentation

### Concerns

- External dependency adds ~6MB to installation size (mitigation: Pydantic is widely adopted and well-maintained, risk is low)
- Developers need to learn Pydantic patterns (mitigation: Pydantic is industry standard with excellent documentation)

## Alternatives

### Stdlib Frozen Dataclasses

Using `@dataclass(frozen=True, slots=True)` from Python's standard library.

- **Pros**: No external dependencies, familiar to Python developers, memory efficient
- **Cons**: No built-in serialization, no validation hooks, would require ~200+ lines of custom serialization code
- **Reason for rejection**: Serialization is a core requirement; implementing it manually adds significant complexity

### attrs + cattrs

Using attrs for data classes and cattrs for serialization.

- **Pros**: Mature library, supports validation, serialization via cattrs
- **Cons**: Less widely adopted than Pydantic, more complex configuration, no built-in schema generation
- **Reason for rejection**: Pydantic has better ecosystem integration and built-in schema generation

### Named Tuples

Using `typing.NamedTuple` for immutable data structures.

- **Pros**: Built-in, immutable by default, lightweight
- **Cons**: Poor ergonomics for models with many fields, no validation hooks, limited extensibility
- **Reason for rejection**: Lack of validation support makes it unsuitable for external data validation

### Custom Classes

Implementing custom classes with manual `__init__`, `__repr__`, `__eq__`, and serialization.

- **Pros**: Full control, no dependencies
- **Cons**: Significant boilerplate, error-prone, no serialization support, manual validation required
- **Reason for rejection**: Too much maintenance burden for functionality that Pydantic provides out-of-the-box

## Future Direction

Enables file-based cassette storage and schema generation for documentation.

Revisit if Pydantic's dependency footprint or validation overhead becomes problematic.

## References

- [Pydantic Documentation](https://docs.pydantic.dev/latest/)
- [Pydantic Performance](https://docs.pydantic.dev/latest/concepts/performance/)
