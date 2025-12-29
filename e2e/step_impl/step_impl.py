"""Step implementations for Gauge tests."""

import shlex
import subprocess

from getgauge.python import data_store, step

from interposition._version import __version__


@step("User types <interposition --version> in terminal")
def user_types_in_terminal(arg1: str) -> None:
    """Execute the interposition command with the given arguments."""
    args = shlex.split(arg1)
    if not args or args[0] != "interposition":
        msg = f"Expected 'interposition' command, got: {arg1}"
        raise ValueError(msg)

    result = subprocess.run(  # noqa: S603
        args,
        capture_output=True,
        text=True,
        check=False,
    )
    data_store.scenario["command_output"] = result.stdout.strip()
    data_store.scenario["command_returncode"] = result.returncode


@step("The output should coincide with interposition's version")
def output_should_coincide_with_version() -> None:
    """Verify that the command output matches the expected version."""
    output = data_store.scenario.get("command_output", "")
    returncode = data_store.scenario.get("command_returncode", 1)

    assert returncode == 0, f"Command failed with return code {returncode}"
    assert output == __version__, f"Expected version {__version__}, got {output}"
