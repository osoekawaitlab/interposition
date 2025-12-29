"""CLI module for interposition."""

from argparse import ArgumentParser

from interposition._version import __version__


def generate_cli_parser() -> ArgumentParser:
    """Generate the argument parser for the interposition CLI."""
    parser = ArgumentParser(
        description=(
            "Protocol-agnostic interaction interposition with lifecycle hooks "
            "for record, replay, and control."
        )
    )
    parser.add_argument("--version", action="version", version=__version__)
    return parser


def main() -> None:
    """Entry point for the interposition command-line interface."""
    parser = generate_cli_parser()
    _ = parser.parse_args()
