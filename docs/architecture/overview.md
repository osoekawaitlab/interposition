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
