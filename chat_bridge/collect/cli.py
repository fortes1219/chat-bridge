"""The `chat-bridge collect [address or path …]` subcommand."""

import argparse
import asyncio
from collections.abc import Sequence
from datetime import date
from functools import partial
from pathlib import Path

from chat_bridge.chat.programs import Program
from chat_bridge.chat.service import PROGRAMS, NoLoginError, choose_program
from chat_bridge.cli import EXIT_NOT_ALL, EXIT_OK, Commands, print_error
from chat_bridge.collect import channels, grouping, pages, service, store
from chat_bridge.collect.closes import ClosesError
from chat_bridge.collect.pages import Page
from chat_bridge.errors import LocalSetupError
from chat_bridge.truth.maker import RunError, ask
from chat_bridge.truth.record import Window
from chat_bridge.truth.rules import read_rules
from chat_bridge.truth.truth_files import TRUTH_FOLDER, folder_events, latest_date

WEB_SCHEMES = ("http://", "https://")
# Each line is shown as it happens: reading waits between requests to a site, so a person sees it
# working rather than a silent terminal.
progress = partial(print, flush=True)


def _count(outcomes: Sequence[service.FileOutcome], kind: str) -> int:
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
    """One run of collecting: events found or sorted, each read once and stored."""

    def __init__(self, until: date | None, chosen: Program) -> None:
        self.program = PROGRAMS[chosen]
        self.name = channels.PROGRAM_NAMES[chosen]
        self.root = store.collected_dir()
        self.rules = read_rules()
        self.reader = pages.Reader(progress=progress)
        self.window = Window(None, until)
        self.left_out = 0
        self.stored = 0

    def keep(self, event_date: date, about: str, read: Sequence[Page]) -> None:
        """Store the event with the pages read for it."""
        if not read:
            self.left_out += 1
            progress(f"  not stored  {about}: none of its pages could be read")
            return
        folder = store.store(
            self.root, event_date, about, self.window.since, self.window.until, read
        )
        if folder is None:
            progress(f"  already stored  {about}")
            return
        self.stored += 1
        progress(f"  stored      {folder.name}  ({len(read)} pages)")

    async def from_channels(self) -> None:
        since = latest_date(TRUTH_FOLDER)
        self.window = Window(since, self.window.until)
        held = channels.held_events(
            folder_events(TRUTH_FOLDER, since), store.stored_events(self.root, since)
        )
        found = await channels.search_events(
            channels.enabled_channels(),
            self.rules,
            self.window,
            held,
            self.program,
            self.name,
            progress,
        )
        _show_refused(found.refused)
        self.left_out += len(found.refused)
        progress(f"Found {len(found.events)} events.")
        for number, event in enumerate(found.events, 1):
            progress(
                f"Event {number} of {len(found.events)}: {event.event_date}  {event.about}"
            )
            if (self.root / store.folder_name(event.event_date, event.pages)).exists():
                progress(f"  already stored  {event.about}")
                continue
            read = self.reader.read_addresses(event.pages)
            kept, moved = event.on_their_sites(read.pages)
            for url, reason in moved:
                progress(f"    not used  {url}: {reason}")
            self.left_out += len(read.refused) + len(moved)
            self.keep(event.event_date, event.about, kept)

    async def from_addresses(self, addresses: list[str]) -> None:
        progress(
            f"Reading {len(addresses)} addresses. A site is asked again only "
            f"{pages.SITE_WAIT_SECONDS:g} seconds after its last request."
        )
        read = self.reader.read_addresses(addresses)
        self.left_out += len(read.refused)
        if not read.pages:
            return
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
        self.left_out += len(groups.refused)
        progress(f"Found {len(groups.events)} events.")
        for event in groups.events:
            progress(f"  {event.event_date}  {event.about}")
            self.keep(event.event_date, event.about, event.pages)


async def _collect(addresses: list[str], until: date | None) -> int:
    """Collect and store events; the number of pages and events left out."""
    run = _Run(until, await choose_program(None))
    if addresses:
        await run.from_addresses(addresses)
    else:
        await run.from_channels()
    progress(f"Stored {run.stored} events in {run.root}.")
    if run.stored:
        progress("Make them into truth files: uv run chat-bridge truth")
    return run.left_out


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
    left_out = 0
    try:
        if not targets or addresses:
            left_out += asyncio.run(_collect(addresses, args.until))
        file_outcomes = _collect_market_moves(paths) if paths else []
    except NoLoginError as error:
        return print_error(str(error))
    except channels.SearchError as error:
        return print_error(f"no event was found: {error}")
    except (RunError, grouping.GroupingError) as error:
        return print_error(f"the pages could not be sorted into events: {error}")
    except ClosesError as error:
        return print_error(
            f"the daily closes could not be read, so no news file was changed: {error}"
        )
    except (store.StoreError, LocalSetupError) as error:
        return print_error(str(error))
    left_out += _count(file_outcomes, "refused")
    return EXIT_NOT_ALL if left_out else EXIT_OK


def register(commands: Commands) -> None:
    collect = commands.add_parser(
        "collect",
        help="collect events with your own logged-in agent, from the channels or from web "
        "addresses, and store them for `truth`; or write the market moves of news files",
        description="With nothing after it, your own logged-in Claude Code or Codex finds the "
        "events the channels in data/channels.json reported since the latest event in "
        "data/truth. Web addresses (pages or feeds) are read and sorted into events instead. "
        "Each event is stored with its pages' text in local_data/collected; make the stored "
        "events into truth files with `chat-bridge truth`. Paths are news files, or folders of "
        "them, whose section of market moves is written from the daily closes.",
    )
    collect.add_argument(
        "targets",
        nargs="*",
        metavar="address-or-path",
        help="a web address (http or https), or a news file or folder; none collects from the "
        "channels",
    )
    collect.add_argument(
        "--until",
        type=date.fromisoformat,
        metavar="YYYY-MM-DD",
        help="collect events up to this date (default: today)",
    )
    collect.set_defaults(handler=_run)
