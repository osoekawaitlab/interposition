"""Unit tests for interposition exports."""

import re

import interposition


def test_interposition_exports_version() -> None:
    """Test that interposition exports the correct version."""
    assert re.match(r"^\d+\.\d+\.\d+$", interposition.__version__)
