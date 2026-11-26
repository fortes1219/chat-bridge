"""One event, from its pages to a truth file in the folder.

The agent with no tool writes a record from the pages; the program checks it; a second run of the
agent judges each statement against its passage. A record that fails goes back to the writing run
once with the reasons. The file is then made in a temporary folder, feature 013's market section
is added from the closes read once for the run, and only then does it go into the folder; its
number conversions are added to the record of conversions after it.
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

from chat_bridge.chat.programs import AnsweringProgram, ProgramError
from chat_bridge.collect import checking, record, service
from chat_bridge.collect.channels import TIME_LIMIT_SECONDS
from chat_bridge.collect.closes import Closes
from chat_bridge.collect.markets import MarketSeries
from chat_bridge.collect.pages import Page
from chat_bridge.collect.record import Again, Record, Source, Window
from chat_bridge.collect.rules import Rules
from chat_bridge.collect.service import Kind
from chat_bridge.collect.truth_files import (
    FolderEvent,
    add_conversions,
    free_path,
    put,
    render,
)

logger = logging.getLogger(__name__)
# The writing run is asked once more with the reasons, as instructor re-asks once by default.
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
    chat's limit. Raises RunError."""
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
    window: Window
    closes: Closes
    listed: MarketSeries
    now: datetime
    example: str | None
    # Where the number conversions are recorded; None to record none.
    conversions_file: Path | None
    progress: Callable[[str], None]
    existing: list[FolderEvent] = field(default_factory=list)

    def _held(self, pages: tuple[Page, ...]) -> FolderEvent | None:
        """The folder's file that already cites every page of the event."""
        return next(
            (
                one
                for one in self.existing
                if all(page.url in one.urls or page.asked in one.urls for page in pages)
            ),
            None,
        )

    async def _ask(
        self, prompt: str, text: str, schema: dict[str, Any], what: str
    ) -> dict[str, Any]:
        try:
            return await ask(self.program, self.name, prompt, text, schema, what)
        except RunError as error:
            raise _Refused(str(error)) from error

    async def _second_reader(self, made: Record) -> tuple[str, ...]:
        listed = checking.statements(made)
        self.progress(f"    checking {len(listed)} statements against their passages")
        reply = await self._ask(
            checking.prompt(),
            checking.question(listed),
            checking.CHECK_SCHEMA,
            "the check",
        )
        try:
            return checking.rejections(reply, listed)
        except checking.CheckError as error:
            raise _Refused(str(error)) from error

    async def _record(
        self, about: str, sources: tuple[Source, ...], held: list[FolderEvent]
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
            self.progress(
                f"    writing with {self.name}"
                + ("" if again is None else ", again with the reasons")
            )
            reply = await self._ask(
                prompt,
                record.question(about, sources, self.window, held, again),
                schema,
                "the writing",
            )
            same = record.same_as(reply, held)
            if same is not None:
                return same
            made, reasons = record.check_record(
                reply, sources, self.rules, self.window, self.now.date()
            )
            if made is not None:
                reasons = await self._second_reader(made)
                if not reasons:
                    return made
            for reason in reasons:
                self.progress(f"      {reason}")
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
        self, about: str, event_date: date, pages: tuple[Page, ...]
    ) -> EventOutcome:
        """Write the event found for `event_date` from its pages, unless the folder has it:
        a file citing all its pages, or a file of that date the agent says it is."""
        if not pages:
            return EventOutcome(about, "refused", "none of its pages could be read")
        held = self._held(pages)
        if held is not None:
            return EventOutcome(
                about, "unchanged", f"the folder has it: {held.path.name}"
            )
        sources = tuple(
            Source(f"s{number}", page) for number, page in enumerate(pages, 1)
        )
        same_day = [one for one in self.existing if one.event_date == event_date]
        try:
            made = await self._record(about, sources, same_day)
            if isinstance(made, FolderEvent):
                return EventOutcome(
                    about, "unchanged", f"the folder has it: {made.path.name}"
                )
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
                self.progress(f"    conversion  {one.original} -> {one.converted}")
        self.existing.append(
            FolderEvent(
                path,
                made.file.event_date,
                made.file.title,
                frozenset(entry.url for entry in made.file.sources),
            )
        )
        return EventOutcome(about, "written", made.file.title, path)
