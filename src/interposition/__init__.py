"""Protocol-agnostic interaction interposition with lifecycle hooks.

Provides record, replay, and control capabilities.
"""

from interposition._version import __version__
from interposition.errors import (
    CassetteSaveError,
    InteractionNotFoundError,
    LiveResponderRequiredError,
)
from interposition.models import (
    Cassette,
    Interaction,
    InteractionRequest,
    InteractionValidationError,
    RequestFingerprint,
    ResponseChunk,
)
from interposition.services import Broker, BrokerMode, CassetteStore
from interposition.stores import JsonFileCassetteStore

__all__ = [
    "Broker",
    "BrokerMode",
    "Cassette",
    "CassetteSaveError",
    "CassetteStore",
    "Interaction",
    "InteractionNotFoundError",
    "InteractionRequest",
    "InteractionValidationError",
    "JsonFileCassetteStore",
    "LiveResponderRequiredError",
    "RequestFingerprint",
    "ResponseChunk",
    "__version__",
]
