"""Storage adapters for cassette persistence."""

from __future__ import annotations

from typing import TYPE_CHECKING

from interposition.errors import CassetteLoadError, CassetteSaveError
from interposition.models import Cassette

if TYPE_CHECKING:
    from pathlib import Path


class JsonFileCassetteStore:
    """File-based cassette store using JSON format.

    Attributes:
        path: Path to the JSON file for cassette storage.
    """

    def __init__(self, path: Path, *, create_if_missing: bool = False) -> None:
        """Initialize store with file path.

        Args:
            path: Path to the JSON file (will be created if doesn't exist).
            create_if_missing: If True, load() returns an empty Cassette
                when the file doesn't exist instead of raising CassetteLoadError.
        """
        self._path = path
        self._create_if_missing = create_if_missing

    @property
    def path(self) -> Path:
        """Get the file path."""
        return self._path

    def load(self) -> Cassette:
        """Load cassette from JSON file.

        Returns:
            Cassette instance loaded from file. If create_if_missing is True
            and the file doesn't exist, returns an empty Cassette.

        Raises:
            CassetteLoadError: If file doesn't exist (and create_if_missing
                is False), file is unreadable, or JSON is invalid.
        """
        try:
            json_str = self._path.read_text(encoding="utf-8")
        except FileNotFoundError as e:
            if self._create_if_missing:
                return Cassette(interactions=())
            raise CassetteLoadError(self._path, e) from e
        except OSError as e:
            raise CassetteLoadError(self._path, e) from e
        try:
            return Cassette.model_validate_json(json_str)
        except Exception as e:
            raise CassetteLoadError(self._path, e) from e

    def save(self, cassette: Cassette) -> None:
        """Save cassette to JSON file.

        Creates parent directories if they don't exist.

        Args:
            cassette: The cassette to persist.

        Raises:
            CassetteSaveError: If file write fails.
        """
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            json_str = cassette.model_dump_json(indent=2)
            self._path.write_text(json_str, encoding="utf-8")
        except OSError as e:
            raise CassetteSaveError(self._path, e) from e
