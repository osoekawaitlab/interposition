# Protocol Adapters Guide

Interposition is a **pure logic engine**. It knows how to store and match interactions, but it doesn't know how to talk to the network or your database.

To bridge this gap, you use **Adapters**.

## What is an Adapter?

An Adapter is a piece of code that sits between your application (or its libraries) and Interposition.

Its responsibilities are:
1.  **Intercept**: Catch the outgoing request (HTTP, SQL, etc.).
2.  **Translate**: Convert that request into an `InteractionRequest`.
3.  **Delegate**: Ask the Interposition `Broker` for a response.
4.  **Return**: Convert the `ResponseChunk`s back into the native response format (e.g., `requests.Response` or SQL rows).

## Implementation Strategies

There are two main ways to implement an adapter, depending on your testing needs.

### 1. Monkey Patching (Internal)

Best for: **Unit Tests**, **Python-only projects**, **No Dependencies**.

In this strategy, you replace a library's internal method (like `urllib.request.OpenerDirector.open` or `sqlalchemy.engine.Connection.execute`) with your own function or handler.

**Pros:**
*   Fast and lightweight.
*   No need to change application configuration (URLs).
*   **Zero external dependencies** (if using standard library).

**Cons:**
*   Only works for Python code running in the same process.
*   Relies on library internals.

[👉 See Example: urllib Adapter](https://github.com/osoekawaitlab/interposition/blob/main/examples/http_urllib_adapter.py)

### 2. Proxy Server (External)

Best for: **E2E Tests**, **External Processes**, **Non-Python Clients**.

In this strategy, you run a small server (a proxy) that Interposition controls. You configure your application to send traffic to this proxy.

**Pros:**
*   **Language Agnostic**: Works with `curl`, Node.js, Go, etc.
*   **Process Agnostic**: Works even if your app runs in a separate Docker container.
*   **Clean**: Does not mess with library internals.

**Cons:**
*   Requires changing application config (e.g., setting `HTTP_PROXY`).
*   Slightly more complex setup.

[👉 See Example: HTTP Proxy Server](https://github.com/osoekawaitlab/interposition/blob/main/examples/http_proxy_adapter.py)

## Why aren't adapters included?

We decided not to include built-in adapters (like `interposition.adapters.requests`) in the core package. 
See [ADR 0006: External Protocol Adapters](../adr/0006-external-adapters.md) for the detailed reasoning.

In short: **We want to keep the core lightweight and protocol-agnostic.** By copying the examples and modifying them, you get full control over exactly how the interception happens.
