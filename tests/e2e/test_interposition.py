"""End-to-end tests for interposition."""

import re
import subprocess


def test_interposition_prints_version() -> None:
    """Test that interposition prints the version."""
    result = subprocess.run(
        ["interposition", "--version"],
        capture_output=True,
        text=True,
        check=True,
    )
    assert re.match(r"^\d+\.\d+\.\d+$", result.stdout.strip())
