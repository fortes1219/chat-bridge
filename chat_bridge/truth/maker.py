"""One stored event, from its pages to a truth file in the folder.

The agent with no tool writes a record from the event's stored pages; the program checks it, and a
record that fails goes back to the agent once with the reasons. The file is then made in a
temporary folder, feature 013's market section is added from the closes read once for the run,
and only then does it go into the folder; its number conversions are added to the record of
conversions after it. Naming the file, writing it, and adding it to the list of the folder's
events happen with no wait between them, so events made at the same time never share a name.
"""

from __future__ import annotations

import asyncio
import logging
import tempfile
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date, datetime
from pathlib import Path
from typing import Any

from chat_bridge.chat import claude_code
from chat_bridge.chat.programs import AnsweringProgram, ProgramError
from chat_bridge.collect import service
from chat_bridge.collect.closes import Closes
from chat_bridge.collect.markets import MarketSeries
from chat_bridge.collect.pages import Page
from chat_bridge.collect.service import Kind
from chat_bridge.truth import record
from chat_bridge.truth.record import Again, Record, Source, Window
from chat_bridge.truth.rules import Rules
from chat_bridge.truth.truth_files import (
    FolderEvent,
    add_conversions,
    free_path,
    put,
    render,
)

logger = logging.getLogger(__name__)
# The limit the chat gives one run of a program.
TIME_LIMIT_SECONDS = claude_code.ANSWER_TIMEOUT_SECONDS
# The record is asked for once more with the reasons, as instructor re-asks once by default.
ATTEMPTS = 2


@dataclass(frozen=True)
class EventOutcome:
    about: str
    kind: Kind
    detail: str
    path: Path | None = None


class RunError(Exception):
    """A run of the agent failed or ran past its limit; the message says which."""


class _Refused(Exception):
    """The event cannot be written; the message says why."""


async def ask(
    program: AnsweringProgram,
    name: str,
    prompt: str,
    text: str,
    schema: dict[str, Any],
    what: str,
) -> dict[str, Any]:
    """One run of the person's program with no tool, for a reply in the schema, within the
    chat's limit. A cancelled run ends with every process it started. Raises RunError."""
    try:
        return await asyncio.wait_for(
            program.reply_in_shape(
                prompt,
                text,
                schema,
                on_start=lambda args: logger.debug("Started %s", args[0]),
            ),
            TIME_LIMIT_SECONDS,
        )
    except TimeoutError:
        raise RunError(
            f"{name} did not finish {what} within {TIME_LIMIT_SECONDS} seconds"
        ) from None
    except ProgramError as error:
        raise RunError(f"{what}: {error}") from error


@dataclass
class Maker:
    """Makes the run's events into files: what each one needs that the run shares."""

    rules: Rules
    folder: Path
    program: AnsweringProgram
    name: str
    closes: Closes
    listed: MarketSeries
    now: datetime
    example: str | None
    # Where the number conversions are recorded; None to record none.
    conversions_file: Path | None
    existing: list[FolderEvent] = field(default_factory=list)

    def held(self, pages: tuple[Page, ...]) -> FolderEvent | None:
        """The folder's file that already cites every page of the event."""
        return next(
            (
                one
                for one in self.existing
                if all(page.url in one.urls or page.asked in one.urls for page in pages)
            ),
            None,
        )

    async def _record(
        self,
        about: str,
        sources: tuple[Source, ...],
        window: Window,
        held: list[FolderEvent],
        tell: Callable[[str], None],
    ) -> Record | FolderEvent:
        """The checked record, or the folder's file the agent says the event already is."""
        prompt = record.system_prompt(self.rules, self.example)
        schema = record.record_schema(
            self.rules,
            [source.id for source in sources],
            [one.path.name for one in held],
        )
        again: Again | None = None
        for attempt in range(1, ATTEMPTS + 1):
            tell(
                f"writing with {self.name}"
                + ("" if again is None else ", again with the reasons")
            )
            try:
                reply = await ask(
                    self.program,
                    self.name,
                    prompt,
                    record.question(about, sources, window, held, again),
                    schema,
                    "the writing",
                )
            except RunError as error:
                raise _Refused(str(error)) from error
            same = record.same_as(reply, held)
            if same is not None:
                return same
            made, reasons = record.check_record(
                reply, sources, self.rules, window, self.now.date()
            )
            if made is not None:
                return made
            for reason in reasons:
                tell(f"  {reason}")
            if attempt == ATTEMPTS:
                raise _Refused(f"{len(reasons)} reasons, listed above")
            again = Again(reply, reasons)
        raise AssertionError("unreachable")

    def _with_market_section(self, text: str, name: str) -> str:
        """The file's text with feature 013's market section, made in a temporary folder."""
        with tempfile.TemporaryDirectory(prefix="chat-bridge-") as folder:
            staged = Path(folder) / name
            staged.write_text(text, encoding="utf-8", newline="\n")
            outcome = service.collect_market_moves(
                [staged], now=self.now, listed=self.listed, closes=self.closes
            )[0]
            if outcome.kind != "written":
                raise _Refused(
                    f"the market section could not be written: {outcome.detail}"
                )
            return staged.read_text(encoding="utf-8")

    async def make(
        self,
        about: str,
        event_date: date,
        pages: tuple[Page, ...],
        window: Window,
        tell: Callable[[str], None] = lambda line: None,
    ) -> EventOutcome:
        """Write the event of `event_date` from its pages, unless the folder has it: a file
        citing all its pages, or a file of that date the agent says it is. `tell` is told what
        happens to this event."""
        if not pages:
            return EventOutcome(about, "refused", "it has no page")
        held = self.held(pages)
        if held is not None:
            return EventOutcome(
                about, "unchanged", f"the folder has it: {held.path.name}"
            )
        sources = tuple(
            Source(f"s{number}", page) for number, page in enumerate(pages, 1)
        )
        same_day = [one for one in self.existing if one.event_date == event_date]
        try:
            made = await self._record(about, sources, window, same_day, tell)
            if isinstance(made, FolderEvent):
                return EventOutcome(
                    about, "unchanged", f"the folder has it: {made.path.name}"
                )
            # From here to the end nothing waits, so no other event runs in between.
            path = free_path(self.folder, made.file.event_date, made.slug)
            text = self._with_market_section(render(made.file), path.name)
        except _Refused as error:
            return EventOutcome(about, "refused", str(error))
        put(path, text)
        if self.conversions_file is not None:
            add_conversions(self.conversions_file, path.stem, made.conversions)
        else:
            # Into another folder than the sample's, the conversions are shown, not recorded.
            for one in made.conversions:
                tell(f"conversion  {one.original} -> {one.converted}")
        self.existing.append(
            FolderEvent(
                path,
                made.file.event_date,
                made.file.title,
                frozenset(entry.url for entry in made.file.sources),
            )
        )
        return EventOutcome(about, "written", made.file.title, path)
