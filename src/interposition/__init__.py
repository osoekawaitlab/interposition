"""Protocol-agnostic interaction interposition with lifecycle hooks.

Provides record, replay, and control capabilities.
"""

from interposition._version import __version__
from interposition.errors import InteractionNotFoundError, LiveResponderRequiredError
from interposition.models import (
    Cassette,
    Interaction,
    InteractionRequest,
    InteractionValidationError,
    RequestFingerprint,
    ResponseChunk,
)
from interposition.services import Broker, BrokerMode

__all__ = [
    "Broker",
    "BrokerMode",
    "Cassette",
    "Interaction",
    "InteractionNotFoundError",
    "InteractionRequest",
    "InteractionValidationError",
    "LiveResponderRequiredError",
    "RequestFingerprint",
    "ResponseChunk",
    "__version__",
]
