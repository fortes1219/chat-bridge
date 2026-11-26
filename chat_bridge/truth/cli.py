"""The `chat-bridge truth` subcommand: the events `collect` stored, made into truth files."""

import argparse
import asyncio
from collections.abc import Sequence
from datetime import UTC, datetime
from functools import partial
from pathlib import Path

from chat_bridge.chat.service import PROGRAMS, NoLoginError, choose_program
from chat_bridge.cli import EXIT_NOT_ALL, EXIT_OK, Commands, print_error
from chat_bridge.collect import service, store
from chat_bridge.collect.channels import PROGRAM_NAMES
from chat_bridge.collect.closes import ClosesError
from chat_bridge.collect.markets import market_series
from chat_bridge.collect.store import StoredEvent, StoreError
from chat_bridge.errors import LocalSetupError
from chat_bridge.truth.maker import EventOutcome, Maker
from chat_bridge.truth.record import Window
from chat_bridge.truth.rules import read_rules
from chat_bridge.truth.truth_files import (
    CONVERSIONS_FILE,
    TRUTH_FOLDER,
    example,
    folder_events,
)

# Runs of the person's program at once: the default of news-briefing-generator, NeMo Curator's
# LLM client and hn-time-capsule's analyze stage.
DEFAULT_WORKERS = 5
# Each line is shown as it happens: every event takes a run of the person's program.
progress = partial(print, flush=True)


def _count(outcomes: Sequence[EventOutcome], kind: str) -> int:
    return sum(1 for outcome in outcomes if outcome.kind == kind)


def _ending(outcome: EventOutcome) -> str:
    if outcome.kind == "written":
        return f"written        {outcome.path}"
    label = "not written" if outcome.kind == "refused" else "already there"
    return f"{label:<13}  {outcome.detail}"


async def _make(folder: Path, limit: int | None, workers: int) -> int:
    """Make the stored events into files in `folder`; the number not written."""
    root = store.collected_dir()
    events = store.stored_events(root)
    if limit is not None:
        events = events[:limit]
    if not events:
        progress(
            f"No stored event in {root}. Collect first: uv run chat-bridge collect"
        )
        return 0
    chosen = await choose_program(None)
    name = PROGRAM_NAMES[chosen]
    listed = market_series()
    now = datetime.now(UTC).replace(microsecond=0)
    progress(
        f"Making {len(events)} stored events into files in {folder} with {name}, at most "
        f"{workers} runs at once. Each event is one run, two when its first record fails "
        "the checks."
    )
    progress("Reading the daily closes for the market sections.")
    closes = service.closes_for([event.event_date for event in events], now, listed)
    in_sample = folder.resolve() == TRUTH_FOLDER.resolve()
    maker = Maker(
        rules=read_rules(),
        folder=folder,
        program=PROGRAMS[chosen],
        name=name,
        closes=closes,
        listed=listed,
        now=now,
        example=example(folder),
        conversions_file=CONVERSIONS_FILE if in_sample else None,
        existing=folder_events(folder, min(event.event_date for event in events)),
    )
    workers_free = asyncio.Semaphore(workers)
    # Events of one date are made one after another, so each is shown the files the ones before
    # it wrote and can say it is one of them; events of different dates run at once.
    one_date_at_a_time = {
        day: asyncio.Lock() for day in {event.event_date for event in events}
    }
    ended: list[tuple[int, StoredEvent, EventOutcome]] = []

    async def make_one(number: int, event: StoredEvent) -> None:
        tag = f"[{number}/{len(events)}]"

        def tell(line: str) -> None:
            progress(f"  {tag} {line}")

        async with one_date_at_a_time[event.event_date], workers_free:
            tell(f"{event.event_date}  {event.about}")
            try:
                pages = event.read_pages()
            except StoreError as error:
                outcome = EventOutcome(event.about, "refused", str(error))
            else:
                window = Window(event.since, event.until)
                outcome = await maker.make(
                    event.about, event.event_date, pages, window, tell
                )
            if outcome.kind != "refused":
                # Made, or the folder has it: what was collected for it is not kept.
                store.remove(root, event)
            ended.append((number, event, outcome))
            progress(f"Event {number} of {len(events)}: {_ending(outcome)}")

    await asyncio.gather(
        *(make_one(number, one) for number, one in enumerate(events, 1))
    )
    outcomes = [outcome for _, _, outcome in ended]
    written = _count(outcomes, "written")
    progress(
        f"Files: {written} written, {_count(outcomes, 'unchanged')} already there, "
        f"{_count(outcomes, 'refused')} not written."
    )
    refused = sorted(
        (number, event) for number, event, outcome in ended if outcome.kind == "refused"
    )
    if refused:
        progress(
            "Not written, kept to be tried again by the next `truth` run, which uses your "
            "subscription again:"
        )
        for number, event in refused:
            progress(
                f"  [{number}] {event.event_date}  {event.about}  ({event.folder.name})"
            )
    if written:
        progress(f"Add them to the knowledge base: uv run chat-bridge ingest {folder}")
    return len(refused)


def _run(args: argparse.Namespace) -> int:
    folder: Path = args.into or TRUTH_FOLDER
    try:
        refused = asyncio.run(_make(folder, args.limit, args.workers))
    except NoLoginError as error:
        return print_error(str(error))
    except ClosesError as error:
        return print_error(
            f"the daily closes could not be read, so no file was written: {error}"
        )
    except (StoreError, LocalSetupError) as error:
        return print_error(str(error))
    return EXIT_NOT_ALL if refused else EXIT_OK


def _positive(text: str) -> int:
    number = int(text)
    if number < 1:
        raise argparse.ArgumentTypeError("must be 1 or more")
    return number


def register(commands: Commands) -> None:
    truth = commands.add_parser(
        "truth",
        help="make the events `collect` stored into truth files with your own logged-in agent",
        description="Each event `collect` stored in local_data/collected is written by your "
        "own logged-in Claude Code or Codex, with no tool, as a file in the format of "
        "docs/truth_format.md, from its stored pages only; the program checks it and adds the "
        "market section. An event made into a file, or that the folder already has, is removed "
        "from local_data/collected; one not written is kept and tried again next time. Add the "
        "files to the knowledge base with `chat-bridge ingest`.",
    )
    truth.add_argument(
        "--into",
        type=Path,
        help="the folder the files go to (default: data/truth)",
    )
    truth.add_argument(
        "--limit",
        type=_positive,
        metavar="N",
        help="make only the first N stored events, to try it first",
    )
    truth.add_argument(
        "--workers",
        type=_positive,
        default=DEFAULT_WORKERS,
        metavar="N",
        help=f"runs of your agent at once (default: {DEFAULT_WORKERS})",
    )
    truth.set_defaults(handler=_run)
