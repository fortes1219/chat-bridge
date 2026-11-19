"""The `chat-bridge` command.

Each feature package that has a `cli` module adds its own subcommands through
`register(commands)`, so a new feature does not change this file. The lookup follows
Django, which finds each app's management commands with pkgutil.
"""

import argparse
import importlib
import importlib.util
import io
import pkgutil
import sys
from collections.abc import Callable
from types import ModuleType
from typing import TypeAlias

import chat_bridge
from chat_bridge import __version__

EXIT_OK = 0
EXIT_NOT_ALL = 1  # The command ran, but not everything succeeded or matched.
EXIT_ERROR = 2

Handler = Callable[[argparse.Namespace], int]
# argparse's subparser action is generic only for type checkers, so the alias is a string.
Commands: TypeAlias = "argparse._SubParsersAction[argparse.ArgumentParser]"


def print_error(message: str) -> int:
    """Print an error for the user and return the error exit code."""
    print(f"chat-bridge: {message}", file=sys.stderr)
    return EXIT_ERROR


def _command_modules() -> list[ModuleType]:
    """The `cli` module of every feature package, in name order."""
    modules: list[ModuleType] = []
    for info in sorted(
        pkgutil.iter_modules(chat_bridge.__path__), key=lambda found: found.name
    ):
        name = f"{chat_bridge.__name__}.{info.name}.cli"
        if info.ispkg and importlib.util.find_spec(name) is not None:
            modules.append(importlib.import_module(name))
    return modules


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="chat-bridge", description="A RAG demo over market news."
    )
    parser.add_argument(
        "--version", action="version", version=f"chat-bridge {__version__}"
    )
    commands = parser.add_subparsers(title="commands")
    for module in _command_modules():
        module.register(commands)
    return parser


def _replace_unencodable_output() -> None:
    """Write a character the output encoding cannot hold as "?" instead of failing.

    On Windows, piped output uses the console code page, such as cp950, which lacks some
    characters. markitdown's command line handles stdout the same way.
    """
    for stream in (sys.stdout, sys.stderr):
        if isinstance(stream, io.TextIOWrapper):
            stream.reconfigure(errors="replace")


def main(argv: list[str] | None = None) -> int:
    _replace_unencodable_output()
    parser = _build_parser()
    args = parser.parse_args(argv)
    handler: Handler | None = getattr(args, "handler", None)
    if handler is None:
        parser.print_help()
        return EXIT_OK
    return handler(args)
