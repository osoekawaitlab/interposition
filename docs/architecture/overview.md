# Architecture Overview

This document provides a high-level overview of architectural decisions made for the interposition project.

## Architecture Decision Records

### [ADR-0001: Use Pydantic v2 for Data Models](../adr/0001-pydantic-for-data-models.md)

**Status**: Accepted | **Date**: 2026-01-05

Use Pydantic v2 BaseModel for all data models to enable serialization, runtime validation, and immutability without custom code.

---

### [ADR-0002: Use SHA-256 for Request Fingerprinting](../adr/0002-sha256-fingerprinting.md)

**Status**: Accepted | **Date**: 2026-01-05

Use SHA-256 hash of canonicalized request fields as fingerprints for efficient and collision-resistant interaction matching.

---

### [ADR-0003: Use Generator Pattern for Response Streaming](../adr/0003-generator-streaming.md)

**Status**: Accepted | **Date**: 2026-01-05

Use Python generators for streaming response chunks to enable lazy evaluation, memory efficiency, and backpressure support.

---

### [ADR-0004: Use First-Match Strategy for Duplicate Interactions](../adr/0004-first-match-strategy.md)

**Status**: Accepted | **Date**: 2026-01-05

When multiple interactions have identical fingerprints, return the first match to ensure deterministic and predictable replay behavior.

---

### [ADR-0005: Build Fingerprint Index for O(1) Lookup](../adr/0005-cassette-index.md)

**Status**: Accepted | **Date**: 2026-01-05

Build an in-memory hash map index from fingerprints to interaction positions at cassette construction time for O(1) lookup performance.

---

### [ADR-0006: External Protocol Adapters Strategy](../adr/0006-external-adapters.md)

**Status**: Accepted | **Date**: 2026-01-10

Keep protocol-specific adapters external to the core package. Users implement adapters suited to their integration strategy (monkey patching, proxy servers, etc.).

---

### [ADR-0007: Broker Mode Parameter for Record Functionality](../adr/0007-broker-mode-parameter.md)

**Status**: Accepted | **Date**: 2026-01-25

Add a mode parameter to the Broker class (replay, record, auto) to determine MISS handling behavior, enabling record functionality.

---

### [ADR-0008: Use Literal Type for Broker Mode Values](../adr/0008-literal-type-for-broker-mode.md)

**Status**: Accepted | **Date**: 2026-01-25

Use typing.Literal with a type alias for broker mode values instead of Enum, for simplicity and Pydantic compatibility.

---

### [ADR-0009: LiveResponder Port for Upstream Forwarding](../adr/0009-live-responder-port.md)

**Status**: Accepted | **Date**: 2026-01-25

Define LiveResponder as a callable port (`Callable[[InteractionRequest], Iterable[ResponseChunk]]`) for protocol-agnostic upstream communication.

---

### [ADR-0010: Buffer Live Responses Before Recording](../adr/0010-record-buffering.md)

**Status**: Accepted | **Date**: 2026-01-25

In record/auto mode on a MISS, fully collect live response chunks before returning any data, then record and return the buffered response.
