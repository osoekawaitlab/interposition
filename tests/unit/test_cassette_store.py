"""Unit tests for CassetteStore implementations."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from interposition.errors import (
    CassetteLoadError,
    CassetteSaveError,
    InterpositionError,
)
from interposition.models import Cassette
from interposition.stores import JsonFileCassetteStore

if TYPE_CHECKING:
    from pathlib import Path

    from tests.unit.conftest import MakeInteractionProtocol


_PERMISSION_ERROR = PermissionError("Permission denied")


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

    def test_load_raises_cassette_load_error_for_missing_file(
        self, tmp_path: Path
    ) -> None:
        """Test that load raises CassetteLoadError for missing file."""
        path = tmp_path / "nonexistent.json"
        store = JsonFileCassetteStore(path)

        with pytest.raises(CassetteLoadError) as exc_info:
            store.load()

        assert exc_info.value.path == path
        assert isinstance(exc_info.value.__cause__, FileNotFoundError)

    def test_load_returns_empty_cassette_when_create_if_missing(
        self, tmp_path: Path
    ) -> None:
        """Test load returns empty Cassette when file missing and create_if_missing."""
        path = tmp_path / "nonexistent.json"
        store = JsonFileCassetteStore(path, create_if_missing=True)

        cassette = store.load()

        assert isinstance(cassette, Cassette)
        assert len(cassette.interactions) == 0

    def test_load_raises_cassette_load_error_for_os_error(
        self, tmp_path: Path, monkeypatch: pytest.MonkeyPatch
    ) -> None:
        """Test that load wraps OSError in CassetteLoadError."""
        path = tmp_path / "cassette.json"
        path.write_text("{}", encoding="utf-8")
        store = JsonFileCassetteStore(path)

        def _raise(*_args: object, **_kwargs: object) -> None:
            raise _PERMISSION_ERROR

        monkeypatch.setattr(type(path), "read_text", _raise)

        with pytest.raises(CassetteLoadError) as exc_info:
            store.load()

        assert exc_info.value.path == path
        assert isinstance(exc_info.value.__cause__, PermissionError)

    def test_load_raises_cassette_load_error_for_corrupted_json(
        self, tmp_path: Path
    ) -> None:
        """Test that load raises CassetteLoadError for invalid JSON."""
        path = tmp_path / "cassette.json"
        path.write_text("{corrupted json", encoding="utf-8")
        store = JsonFileCassetteStore(path)

        with pytest.raises(CassetteLoadError) as exc_info:
            store.load()

        assert exc_info.value.path == path

    def test_load_raises_for_corrupted_json_with_create_if_missing(
        self, tmp_path: Path
    ) -> None:
        """Test corrupted JSON raises CassetteLoadError even with create_if_missing."""
        path = tmp_path / "cassette.json"
        path.write_text("{corrupted json", encoding="utf-8")
        store = JsonFileCassetteStore(path, create_if_missing=True)

        with pytest.raises(CassetteLoadError) as exc_info:
            store.load()

        assert exc_info.value.path == path

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

    def test_save_raises_cassette_save_error_on_write_failure(
        self, tmp_path: Path
    ) -> None:
        """Test that save raises CassetteSaveError when write fails."""
        # Use existing directory as file path - can't write file to directory
        path = tmp_path
        store = JsonFileCassetteStore(path)
        cassette = Cassette(interactions=())

        with pytest.raises(CassetteSaveError) as exc_info:
            store.save(cassette)

        assert exc_info.value.path == path
        assert isinstance(exc_info.value.__cause__, OSError)

    def test_cassette_save_error_message_includes_path(self, tmp_path: Path) -> None:
        """Test that CassetteSaveError message includes the file path."""
        # Use existing directory as file path - can't write file to directory
        path = tmp_path
        store = JsonFileCassetteStore(path)
        cassette = Cassette(interactions=())

        with pytest.raises(CassetteSaveError, match=str(path)):
            store.save(cassette)


class TestCassetteLoadError:
    """Test suite for CassetteLoadError."""

    def test_stores_path(self, tmp_path: Path) -> None:
        """Test that exception stores the path."""
        path = tmp_path / "cassette.json"
        cause = FileNotFoundError("not found")
        error = CassetteLoadError(path, cause)

        assert error.path == path

    def test_stores_cause(self, tmp_path: Path) -> None:
        """Test that exception stores the original cause."""
        path = tmp_path / "cassette.json"
        cause = FileNotFoundError("not found")
        error = CassetteLoadError(path, cause)

        assert error.__cause__ is cause

    def test_error_message_includes_path(self, tmp_path: Path) -> None:
        """Test that error message includes the file path."""
        path = tmp_path / "cassette.json"
        cause = FileNotFoundError("not found")
        error = CassetteLoadError(path, cause)

        assert str(path) in str(error)

    def test_inherits_from_interposition_error(self, tmp_path: Path) -> None:
        """Test that CassetteLoadError inherits from InterpositionError."""
        path = tmp_path / "cassette.json"
        cause = FileNotFoundError("not found")
        error = CassetteLoadError(path, cause)

        assert isinstance(error, InterpositionError)


class TestCassetteSaveError:
    """Test suite for CassetteSaveError."""

    def test_stores_path(self, tmp_path: Path) -> None:
        """Test that exception stores the path."""
        path = tmp_path / "cassette.json"
        cause = PermissionError("denied")
        error = CassetteSaveError(path, cause)

        assert error.path == path

    def test_stores_cause(self, tmp_path: Path) -> None:
        """Test that exception stores the original cause."""
        path = tmp_path / "cassette.json"
        cause = PermissionError("denied")
        error = CassetteSaveError(path, cause)

        assert error.__cause__ is cause

    def test_error_message_includes_path(self, tmp_path: Path) -> None:
        """Test that error message includes the file path."""
        path = tmp_path / "cassette.json"
        cause = PermissionError("denied")
        error = CassetteSaveError(path, cause)

        assert str(path) in str(error)

    def test_inherits_from_interposition_error(self, tmp_path: Path) -> None:
        """Test that CassetteSaveError inherits from InterpositionError."""
        path = tmp_path / "cassette.json"
        cause = PermissionError("denied")
        error = CassetteSaveError(path, cause)

        assert isinstance(error, InterpositionError)
