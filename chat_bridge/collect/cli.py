"""The `chat-bridge collect <address or path> …` subcommand."""

import argparse
from collections.abc import Sequence
from functools import partial
from pathlib import Path

from chat_bridge.cli import EXIT_NOT_ALL, EXIT_OK, Commands, print_error
from chat_bridge.collect import pages, service
from chat_bridge.collect.closes import ClosesError
from chat_bridge.config import local_data_dir
from chat_bridge.errors import LocalSetupError

WEB_SCHEMES = ("http://", "https://")
# Each line is shown as it happens: collecting waits between requests to a site, so a person
# sees it working rather than a silent terminal.
progress = partial(print, flush=True)


def default_folder() -> Path:
    return local_data_dir() / "collected"


def _count(outcomes: Sequence[pages.Outcome | service.FileOutcome], kind: str) -> int:
    return sum(1 for outcome in outcomes if outcome.kind == kind)


def _collect_pages(addresses: list[str], folder: Path) -> list[pages.Outcome]:
    progress(
        f"Collecting {len(addresses)} addresses into {folder}. A site is asked again only "
        f"{pages.SITE_WAIT_SECONDS:g} seconds after its last request, so a feed's items take "
        "a while."
    )
    outcomes = pages.collect_addresses(addresses, folder, progress=progress)
    progress(
        f"Pages: {_count(outcomes, 'written')} written, "
        f"{_count(outcomes, 'unchanged')} unchanged, "
        f"{_count(outcomes, 'refused')} not collected."
    )
    if _count(outcomes, "written"):
        progress(
            f"To add them to the knowledge base: uv run chat-bridge ingest {folder}"
        )
    return outcomes


def _collect_market_moves(paths: list[Path]) -> list[service.FileOutcome]:
    files = service.news_paths(paths)
    progress(f"Market moves of {len(files)} news files: reading the daily closes.")
    outcomes = service.collect_market_moves(files)
    for outcome in outcomes:
        detail = f": {outcome.detail}" if outcome.detail else ""
        label = "not done" if outcome.kind == "refused" else outcome.kind
        progress(f"  {label:<9}  {outcome.path}{detail}")
    progress(
        f"Market moves: {_count(outcomes, 'written')} written, "
        f"{_count(outcomes, 'unchanged')} unchanged, "
        f"{_count(outcomes, 'refused')} not done."
    )
    return outcomes


def _run(args: argparse.Namespace) -> int:
    targets: list[str] = args.targets
    addresses = [target for target in targets if target.startswith(WEB_SCHEMES)]
    paths = [Path(target) for target in targets if not target.startswith(WEB_SCHEMES)]
    missing = [path for path in paths if not path.exists()]
    if missing:
        return print_error(
            "not a web address and not a file or folder here: "
            + ", ".join(str(path) for path in missing)
        )
    folder: Path = args.into or default_folder()
    page_outcomes = _collect_pages(addresses, folder) if addresses else []
    try:
        file_outcomes = _collect_market_moves(paths) if paths else []
    except ClosesError as error:
        return print_error(
            f"the daily closes could not be read, so no news file was changed: {error}"
        )
    except LocalSetupError as error:
        return print_error(str(error))
    refused = _count(page_outcomes, "refused") + _count(file_outcomes, "refused")
    return EXIT_NOT_ALL if refused else EXIT_OK


def register(commands: Commands) -> None:
    collect = commands.add_parser(
        "collect",
        help="collect web pages and feeds into a folder for `ingest`, and the market moves of "
        "news files",
        description="Web addresses are collected as pages, or as feeds when they are feeds, into "
        "local_data/collected/ (or --into). Paths are news files, or folders of them, whose "
        "section of market moves is written from the daily closes.",
    )
    collect.add_argument(
        "targets",
        nargs="+",
        metavar="address-or-path",
        help="a web address (http or https), or a news file or folder",
    )
    collect.add_argument(
        "--into",
        type=Path,
        help="the folder collected pages go to (default: local_data/collected)",
    )
    collect.set_defaults(handler=_run)
