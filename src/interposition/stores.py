"""Storage adapters for cassette persistence."""

from __future__ import annotations

from typing import TYPE_CHECKING

from interposition.models import Cassette

if TYPE_CHECKING:
    from pathlib import Path


class JsonFileCassetteStore:
    """File-based cassette store using JSON format.

    Attributes:
        path: Path to the JSON file for cassette storage.
    """

    def __init__(self, path: Path) -> None:
        """Initialize store with file path.

        Args:
            path: Path to the JSON file (will be created if doesn't exist).
        """
        self._path = path

    @property
    def path(self) -> Path:
        """Get the file path."""
        return self._path

    def load(self) -> Cassette:
        """Load cassette from JSON file.

        Returns:
            Cassette instance loaded from file.

        Raises:
            FileNotFoundError: If file doesn't exist.
            pydantic.ValidationError: If JSON is invalid.
        """
        json_str = self._path.read_text(encoding="utf-8")
        return Cassette.model_validate_json(json_str)

    def save(self, cassette: Cassette) -> None:
        """Save cassette to JSON file.

        Creates parent directories if they don't exist.

        Args:
            cassette: The cassette to persist.
        """
        self._path.parent.mkdir(parents=True, exist_ok=True)
        json_str = cassette.model_dump_json(indent=2)
        self._path.write_text(json_str, encoding="utf-8")
