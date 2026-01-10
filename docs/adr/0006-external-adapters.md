# ADR 0006: External Protocol Adapters Strategy

## Status

Accepted

## Date

2026-01-10

## Context

Interposition is designed to be a protocol-agnostic logic engine for recording and replaying interactions.

Users integrate Interposition with various consumers. These include:

- **Python libraries**: e.g., `requests`, `psycopg2`, `boto3`.
- **External processes**: e.g., `curl` commands, `psql` clients, or applications written in other languages (Node.js, Go).

A key architectural decision is whether to include specific adapters for these use cases within the core `interposition` package or to keep them separate.

## Decision

We will **NOT** include protocol-specific adapters in the core `interposition` package.

Adapters must be:

1. Implemented by the user or provided as separate packages.
2. Capable of using the strategy best suited for the target (e.g., **Monkey Patching** for simple Python unit tests, **Proxy Servers** for black-box E2E tests).

The core package will remain a pure logic engine with minimal dependencies.

## Rationale

- **Diverse Integration Strategies**: Different contexts require different integration methods. A unit test might prefer a lightweight monkey patch on `requests`, while an E2E test requires a transparent HTTP proxy to intercept traffic from a subprocess. The core engine should not dictate the integration strategy.
- **Separation of Concerns**: Interposition handles *what* to replay. The Adapter handles *how* to intercept it.
- **Dependency Management**: Including adapters for every possible library and protocol would bloat the core package.
- **Release Independence**: The core engine should not need updates when external libraries change.

## Implications

### Positive Implications

- **Flexibility**: Users can choose to implement a Proxy, a Monkey Patch, or a Decorator based on their testing needs.
- **Lightweight Core**: `pip install interposition` remains small and fast.
- **E2E Support**: Explicitly designing for "external adapters" encourages the creation of proxy-based tools that enable language-agnostic testing.

### Concerns

- **Onboarding Friction**: Users need to write glue code to get started (Mitigation: Provide high-quality "Reference Implementations" in `examples/` for both strategies, e.g., a `requests` patcher AND a simple HTTP proxy).

## Alternatives

### Include Common Adapters (e.g., `requests`) in Core

Include adapters for the most popular libraries (like `requests`) in the main package.

- **Pros**: Easier onboarding for the majority of users.
- **Cons**: Increases maintenance burden and dependency graph.
- **Reason for Rejection**: Violates the strict separation of concerns.

### Monorepo with Multiple Packages

Manage core and adapters in a single monorepo but publish them as separate PyPI packages (`interposition`, `interposition-requests`, etc.).

- **Pros**: Centralized management, separate dependencies.
- **Cons**: Higher complexity in CI/CD and release processes.
- **Reason for Rejection**: Premature complexity. We will start with Reference Implementations and consider separate packages if demand grows.

## Future Direction

We will create an `examples/` directory to house high-quality reference adapters. If a specific adapter becomes extremely popular and stable, we may consider adopting it as an official separate package (e.g., `interposition-requests`) under the same organization, but it will remain distinct from the core.

## References

- [OpenTelemetry Architecture](https://opentelemetry.io/docs/specs/otel/overview/) (Separation of API/SDK from Instrumentation)
