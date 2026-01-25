# API Reference

This page documents the public API of the interposition library.

## Core Module

::: interposition
    options:
      members:
        - Broker
        - BrokerMode
        - Cassette
        - Interaction
        - InteractionRequest
        - ResponseChunk
        - RequestFingerprint
        - InteractionNotFoundError
        - InteractionValidationError
        - LiveResponderRequiredError

## Services

::: interposition.services.Broker
    options:
      show_root_heading: true
      heading_level: 3

## Models

### Cassette

::: interposition.models.Cassette
    options:
      show_root_heading: false
      heading_level: 4

### Interaction

::: interposition.models.Interaction
    options:
      show_root_heading: false
      heading_level: 4

### InteractionRequest

::: interposition.models.InteractionRequest
    options:
      show_root_heading: false
      heading_level: 4

### ResponseChunk

::: interposition.models.ResponseChunk
    options:
      show_root_heading: false
      heading_level: 4

### RequestFingerprint

::: interposition.models.RequestFingerprint
    options:
      show_root_heading: false
      heading_level: 4

## Exceptions

### InteractionNotFoundError

::: interposition.errors.InteractionNotFoundError
    options:
      show_root_heading: false
      heading_level: 4

### InteractionValidationError

::: interposition.models.InteractionValidationError
    options:
      show_root_heading: false
      heading_level: 4

### LiveResponderRequiredError

::: interposition.errors.LiveResponderRequiredError
    options:
      show_root_heading: false
      heading_level: 4
