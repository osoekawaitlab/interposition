# ADR 0008: Use Literal Type for Broker Mode Values

## Status

Accepted

## Date

2026-01-25

## Context

ADR 0007 introduced a mode parameter to the Broker class. The mode accepts one of three string values: "replay", "record", or "auto".

The mode value must be type-safe and provide good developer experience. Two approaches are available in Python for representing a fixed set of string values:

1. `typing.Literal["replay", "record", "auto"]`
2. `enum.Enum` subclass (e.g., `class BrokerMode(str, Enum)`)

## Decision

Use `typing.Literal` with a type alias for the broker mode.

## Rationale

- **Consistency with typing-first design**: Literal types integrate with mypy and keep the API lightweight without extra runtime machinery.
- **Simplicity**: Literal types require no class definition, reducing boilerplate.
- **String compatibility**: Literal values are plain strings, making serialization trivial and API usage straightforward.
- **Type safety**: Both approaches provide equivalent static type checking via mypy.

## Implications

### Positive Implications

- Mode values can be passed as plain strings without imports.
- JSON serialization works without custom encoders.
- Less code to maintain.

### Concerns

- IDE autocompletion may be slightly less discoverable than Enum members (mitigation: type alias makes the valid values explicit in documentation and type hints).
- No runtime validation by default (mitigation: rely on static type checking and clear documentation).

## Alternatives

### Enum Type

Using `class BrokerMode(str, Enum): REPLAY = "replay" ...`

- **Pros**: Strong IDE autocompletion, explicit namespace for values, runtime validation built-in.
- **Cons**: Requires import, additional boilerplate, serialization needs `.value` access.
- **Reason for rejection**: The additional ceremony does not provide sufficient benefit for this use case.

## Future Direction

Revisit if:

- Mode values need associated behavior (methods on the enum).
- Runtime validation outside Pydantic becomes necessary.
- The number of modes grows significantly.

## References

- ADR 0007: Broker Mode Parameter for Record Functionality
- [typing.Literal documentation](https://docs.python.org/3/library/typing.html#typing.Literal)
- [Pydantic Literal types](https://docs.pydantic.dev/latest/concepts/types/#literal-types)
