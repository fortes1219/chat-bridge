"""The `chat-bridge collect [address or path …]` subcommand."""

import argparse
import asyncio
from collections.abc import Sequence
from dataclasses import dataclass
from datetime import UTC, date, datetime
from functools import partial
from pathlib import Path

from chat_bridge.chat.programs import Program
from chat_bridge.chat.service import PROGRAMS, NoLoginError, choose_program
from chat_bridge.cli import EXIT_NOT_ALL, EXIT_OK, Commands, print_error
from chat_bridge.collect import channels, grouping, pages, service
from chat_bridge.collect.closes import ClosesError
from chat_bridge.collect.markets import market_series
from chat_bridge.collect.pages import Page
from chat_bridge.collect.record import Window
from chat_bridge.collect.rules import read_rules
from chat_bridge.collect.truth import EventOutcome, Maker, RunError, ask
from chat_bridge.collect.truth_files import (
    CONVERSIONS_FILE,
    TRUTH_FOLDER,
    example,
    folder_events,
    latest_date,
)
from chat_bridge.errors import LocalSetupError

WEB_SCHEMES = ("http://", "https://")
# Each line is shown as it happens: reading waits between requests to a site and each event takes
# the agent's runs, so a person sees it working rather than a silent terminal.
progress = partial(print, flush=True)


@dataclass(frozen=True)
class _Event:
    """An event to write: its pages read already (from addresses), or the event the channels'
    search found, whose pages are read when its turn comes."""

    event_date: date
    about: str
    found: channels.FoundEvent | None = None
    pages: tuple[Page, ...] = ()

    @property
    def page_count(self) -> int:
        return len(self.found.pages) if self.found is not None else len(self.pages)


def _count(outcomes: Sequence[EventOutcome | service.FileOutcome], kind: str) -> int:
    return sum(1 for outcome in outcomes if outcome.kind == kind)


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


def _show_refused(refused: Sequence[tuple[str, str]]) -> None:
    for what, reason in refused:
        progress(f"  not used  {what}: {reason}")


class _Run:
    """One run of collecting events into the folder, with the person's chosen program."""

    def __init__(self, folder: Path, until: date | None, program: Program) -> None:
        self.folder = folder
        self.program = PROGRAMS[program]
        self.name = channels.PROGRAM_NAMES[program]
        self.rules = read_rules()
        self.listed = market_series()
        self.now = datetime.now(UTC).replace(microsecond=0)
        self.reader = pages.Reader(progress=progress)
        self.window = Window(None, until)
        self.refused = 0

    async def from_channels(self) -> list[_Event]:
        since = latest_date(self.folder)
        self.window = Window(since, self.window.until)
        found = await channels.search_events(
            channels.enabled_channels(),
            self.rules,
            self.window,
            folder_events(self.folder, since),
            self.program,
            self.name,
            progress,
        )
        _show_refused(found.refused)
        self.refused += len(found.refused)
        return [_Event(one.event_date, one.about, found=one) for one in found.events]

    async def from_addresses(self, addresses: list[str]) -> list[_Event]:
        progress(
            f"Reading {len(addresses)} addresses. A site is asked again only "
            f"{pages.SITE_WAIT_SECONDS:g} seconds after its last request."
        )
        read = self.reader.read_addresses(addresses)
        self.refused += len(read.refused)
        if not read.pages:
            return []
        numbered = grouping.numbered(read.pages)
        progress(
            f"Asking {self.name} to sort {len(numbered)} pages into events on the "
            "collection targets."
        )
        reply = await ask(
            self.program,
            self.name,
            grouping.prompt(),
            grouping.question(numbered, self.rules, self.window),
            grouping.groups_schema(list(numbered)),
            "the sorting",
        )
        groups = grouping.read_groups(reply, numbered, self.window)
        _show_refused(groups.refused)
        self.refused += len(groups.refused)
        return [
            _Event(one.event_date, one.about, pages=one.pages) for one in groups.events
        ]

    def _pages(self, event: _Event) -> tuple[Page, ...]:
        """The event's pages: read now for a channel's event, each still on its channel's site
        after any redirect."""
        if event.found is None:
            return event.pages
        read = self.reader.read_addresses(event.found.pages)
        kept, moved = event.found.on_their_sites(read.pages)
        for url, reason in moved:
            progress(f"    not used  {url}: {reason}")
        self.refused += len(read.refused) + len(moved)
        return kept

    async def write(self, events: list[_Event]) -> list[EventOutcome]:
        dates = [event.event_date for event in events]
        progress("Reading the daily closes for the market sections.")
        closes = service.closes_for(dates, self.now, self.listed)
        in_sample = self.folder.resolve() == TRUTH_FOLDER.resolve()
        maker = Maker(
            rules=self.rules,
            folder=self.folder,
            program=self.program,
            name=self.name,
            window=self.window,
            closes=closes,
            listed=self.listed,
            now=self.now,
            example=example(self.folder),
            conversions_file=CONVERSIONS_FILE if in_sample else None,
            progress=progress,
            existing=folder_events(self.folder, min(dates)),
        )
        outcomes: list[EventOutcome] = []
        for number, event in enumerate(events, 1):
            progress(
                f"Event {number} of {len(events)}: {event.event_date}  {event.about}"
            )
            outcome = await maker.make(
                event.about, event.event_date, self._pages(event)
            )
            outcomes.append(outcome)
            if outcome.kind == "written":
                progress(f"  written        {outcome.path}")
            else:
                label = "not written" if outcome.kind == "refused" else "already there"
                progress(f"  {label:<13}  {outcome.detail}")
        return outcomes


async def _collect_events(
    addresses: list[str], folder: Path, until: date | None
) -> int:
    """Collect events into the folder; the number of pages and events not used."""
    run = _Run(folder, until, await choose_program(None))
    events = (
        await run.from_addresses(addresses) if addresses else await run.from_channels()
    )
    progress(f"Found {len(events)} events.")
    for event in events:
        progress(f"  {event.event_date}  {event.about}  ({event.page_count} pages)")
    if not events:
        return run.refused
    outcomes = await run.write(events)
    written = _count(outcomes, "written")
    progress(
        f"Files: {written} written, "
        f"{_count(outcomes, 'unchanged')} already there, "
        f"{_count(outcomes, 'refused')} not written."
    )
    if written:
        progress(f"Add them to the knowledge base: uv run chat-bridge ingest {folder}")
    return run.refused + _count(outcomes, "refused")


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
    folder: Path = args.into or TRUTH_FOLDER
    refused = 0
    try:
        if not targets or addresses:
            refused += asyncio.run(_collect_events(addresses, folder, args.until))
        file_outcomes = _collect_market_moves(paths) if paths else []
    except NoLoginError as error:
        return print_error(str(error))
    except channels.SearchError as error:
        return print_error(f"no event was found: {error}")
    except (RunError, grouping.GroupingError) as error:
        return print_error(f"the pages could not be sorted into events: {error}")
    except ClosesError as error:
        return print_error(
            f"the daily closes could not be read, so no file was written: {error}"
        )
    except LocalSetupError as error:
        return print_error(str(error))
    refused += _count(file_outcomes, "refused")
    return EXIT_NOT_ALL if refused else EXIT_OK


def register(commands: Commands) -> None:
    collect = commands.add_parser(
        "collect",
        help="collect events into truth files with your own logged-in agent, from the "
        "channels or from web addresses; or write the market moves of news files",
        description="With nothing after it, your own logged-in Claude Code or Codex finds the "
        "events the channels in data/channels.json reported since the folder's latest event, "
        "and each event is written as a file in the format of docs/truth_format.md. Web "
        "addresses (pages or feeds) are read and sorted into events the same way. The files go "
        "to data/truth (or --into); add them to the knowledge base with `chat-bridge ingest`. "
        "Paths are news files, or folders of them, whose section of market moves is written "
        "from the daily closes.",
    )
    collect.add_argument(
        "targets",
        nargs="*",
        metavar="address-or-path",
        help="a web address (http or https), or a news file or folder; none collects from the "
        "channels",
    )
    collect.add_argument(
        "--into",
        type=Path,
        help="the folder the files go to (default: data/truth)",
    )
    collect.add_argument(
        "--until",
        type=date.fromisoformat,
        metavar="YYYY-MM-DD",
        help="collect events up to this date (default: today)",
    )
    collect.set_defaults(handler=_run)
