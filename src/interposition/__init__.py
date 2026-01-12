"""Protocol-agnostic interaction interposition with lifecycle hooks.

Provides record, replay, and control capabilities.
"""

from interposition._version import __version__
from interposition.errors import InteractionNotFoundError
from interposition.models import (
    Cassette,
    Interaction,
    InteractionRequest,
    InteractionValidationError,
    RequestFingerprint,
    ResponseChunk,
)
from interposition.services import Broker

__all__ = [
    "Broker",
    "Cassette",
    "Interaction",
    "InteractionNotFoundError",
    "InteractionRequest",
    "InteractionValidationError",
    "RequestFingerprint",
    "ResponseChunk",
    "__version__",
]
