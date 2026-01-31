"""Unit tests for CassetteStore implementations."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from interposition.models import Cassette
from interposition.stores import JsonFileCassetteStore

if TYPE_CHECKING:
    from pathlib import Path

    from tests.unit.conftest import MakeInteractionProtocol


class TestJsonFileCassetteStore:
    """Test suite for JsonFileCassetteStore."""

    def test_path_property(self, tmp_path: Path) -> None:
        """Test that path property returns the configured path."""
        path = tmp_path / "cassette.json"
        store = JsonFileCassetteStore(path)
        assert store.path == path

    def test_save_creates_file(
        self, tmp_path: Path, make_interaction: MakeInteractionProtocol
    ) -> None:
        """Test that save creates a JSON file."""
        path = tmp_path / "cassette.json"
        store = JsonFileCassetteStore(path)
        cassette = Cassette(interactions=(make_interaction(),))

        store.save(cassette)

        assert path.exists()
        assert path.read_text(encoding="utf-8").startswith("{")

    def test_save_creates_parent_directories(
        self, tmp_path: Path, make_interaction: MakeInteractionProtocol
    ) -> None:
        """Test that save creates parent directories if needed."""
        path = tmp_path / "nested" / "dirs" / "cassette.json"
        store = JsonFileCassetteStore(path)
        cassette = Cassette(interactions=(make_interaction(),))

        store.save(cassette)

        assert path.exists()

    def test_load_returns_cassette(
        self, tmp_path: Path, make_interaction: MakeInteractionProtocol
    ) -> None:
        """Test that load returns a Cassette instance."""
        path = tmp_path / "cassette.json"
        store = JsonFileCassetteStore(path)
        original = Cassette(interactions=(make_interaction(),))
        store.save(original)

        loaded = store.load()

        assert isinstance(loaded, Cassette)

    def test_load_raises_file_not_found(self, tmp_path: Path) -> None:
        """Test that load raises FileNotFoundError for missing file."""
        path = tmp_path / "nonexistent.json"
        store = JsonFileCassetteStore(path)

        with pytest.raises(FileNotFoundError):
            store.load()

    def test_roundtrip_serialization(
        self, tmp_path: Path, make_interaction: MakeInteractionProtocol
    ) -> None:
        """Test that save then load preserves cassette data."""
        path = tmp_path / "cassette.json"
        store = JsonFileCassetteStore(path)
        interaction = make_interaction()
        original = Cassette(interactions=(interaction,))

        store.save(original)
        loaded = store.load()

        assert len(loaded.interactions) == 1
        assert loaded.interactions[0].request == interaction.request
        assert loaded.interactions[0].fingerprint == interaction.fingerprint
        assert loaded.interactions[0].response_chunks == interaction.response_chunks

    def test_save_overwrites_existing(
        self, tmp_path: Path, make_interaction: MakeInteractionProtocol
    ) -> None:
        """Test that save replaces existing file content."""
        path = tmp_path / "cassette.json"
        store = JsonFileCassetteStore(path)
        first = Cassette(interactions=(make_interaction(),))
        second = Cassette(interactions=())

        store.save(first)
        store.save(second)
        loaded = store.load()

        assert len(loaded.interactions) == 0

    def test_empty_cassette_roundtrip(self, tmp_path: Path) -> None:
        """Test that empty cassette can be saved and loaded."""
        path = tmp_path / "cassette.json"
        store = JsonFileCassetteStore(path)
        original = Cassette(interactions=())

        store.save(original)
        loaded = store.load()

        assert len(loaded.interactions) == 0

    def test_loaded_cassette_has_working_index(
        self, tmp_path: Path, make_interaction: MakeInteractionProtocol
    ) -> None:
        """Test that loaded cassette has a functional fingerprint index."""
        path = tmp_path / "cassette.json"
        store = JsonFileCassetteStore(path)
        interaction = make_interaction()
        original = Cassette(interactions=(interaction,))

        store.save(original)
        loaded = store.load()

        found = loaded.find_interaction(interaction.fingerprint)
        assert found is not None
        assert found.request == interaction.request
