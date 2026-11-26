---
description: "Task list for collect making truth files"
---

# Tasks: Collect makes truth files as the 71 were made

**Input**: Design documents from `specs/016-collect-into-truth/`

**Prerequisites**: plan.md, spec.md, research.md (with its `## Packages` and `## Advisories`)

**Tests**: Fast tests use stand-in agents, stand-in pages and stand-in closes, and reach no network
and start no program. The smallest real run starts the person's own program, only with the
maintainer's consent.

One commit the maintainer makes, after the checks.

- [x] T001 `chat_bridge/collect/rules.py`: the targets, headings, keys and exposure words read from the two docs, the markets from `data/market_series.json`; a doc that yields none stops the command (FR-002).
- [x] T002 `chat_bridge/collect/pages.py`: pages and feed items read into plain text with title, site and date; no file written; an item whose page cannot be read is named (FR-005, FR-008).
- [x] T003 `chat_bridge/collect/truth_files.py`: the folder's files from the start date (dates, titles, cited pages), the file name, a record written in the 71 files' layout; a test writes the front matter of sample files from their own values and gets their bytes (FR-001).
- [x] T004 `chat_bridge/collect/record.py`, `writing_prompt.md`: the schema built from the rules, the writing question, and each check of User Story 1 scenario 5 (FR-003, FR-004).
- [x] T005 `chat_bridge/collect/checking.py`, `checking_prompt.md`: the second reader's question and its answer read; one rejected item refuses the file (FR-003a).
- [x] T006 `chat_bridge/collect/channels.py`, `channels_prompt.md`: events with source pages from the channels, the start date from the folder, `--until`, the folder's events given (User Story 1 scenario 1, User Story 3).
- [x] T007 `chat_bridge/collect/grouping.py`, `grouping_prompt.md`: given pages sorted into events, pages that bear on none named (User Story 2).
- [x] T008 `chat_bridge/collect/truth.py`: one event from pages to a file: write, check, second reader, market section from the closes read once, into the folder, conversions added; an event already written is not written (User Story 1 scenarios 2 to 6, FR-006).
- [x] T009 `chat_bridge/collect/cli.py`: `data/truth` by default, `--until`, no ingest, the progress lines and the closing ingest command (User Story 1 scenario 7, FR-007, FR-008).
- [x] T010 [P] Tests: SC-001 and SC-002 with saved pages and stand-in records; the command with stand-ins from the channels and from addresses.
- [x] T011 `README.md`, `README_tzh.md`, `docs/truth_format.md` section 7 (FR-007).
- [x] T012 Checks (ruff, ruff format, mypy, fast suite), `git ls-files --eol`; hand the work to the reviewer.
- [x] T013 (first version) Ask the maintainer for consent, then the smallest real run (SC-003) through `uv run chat-bridge collect <one article address> --into <a copy of data/truth>`; keep the terminal output and the seconds, set the file beside an earlier one section by section, record it in research.md and the README's time and cost.
- [x] T014 The file list and one commit message to the maintainer, saying what feature 013's collected pages and feature 015's ingest became.

## Second version: two steps (after the maintainer's first full run)

One fix commit the maintainer makes, after the checks.

- [x] T015 `chat_bridge/collect/store.py`: an event's folder named from its date and pages, `event.json` and the pages' text written whole, read back, the stored events from a date, removed only when it is a stored event of the collected folder (FR-010, User Story 3 scenario 4, SC-005).
- [x] T016 `chat_bridge/collect/cli.py`, `channels.py`: `collect` stores each event it finds or sorts, reads each page once, tells the search the stored events too, writes no truth file, ends with the `truth` command (User Stories 1 and 2).
- [x] T017 Move the making of files into `chat_bridge/truth/` (`maker.py`, `record.py`, `rules.py`, `truth_files.py`, `writing_prompt.md`); remove the second reader (`collect/checking.py`, `checking_prompt.md`) (FR-008).
- [x] T018 `chat_bridge/truth/cli.py`: `truth` with `--into`, `--limit`, `--workers`; the stored events, the closes read once, at most `--workers` events at once, the stored folder removed once the event is done, the events not written listed at the end, the ingest line when a file was written (User Story 3).
- [x] T019 [P] Tests: SC-001 to SC-005 with stand-ins (stored pages, stand-in runs that wait, a stop while two runs are under way).
- [x] T020 `README.md`, `README_tzh.md`, `docs/truth_format.md`: the three commands in order, where events are stored and that they are removed once made, the model runs and how many at once, the retries' cost (FR-007).
- [x] T021 Checks (ruff, ruff format, mypy, fast suite), `git ls-files --eol`; hand the work to the reviewer.
- [ ] T022 Ask the maintainer for consent, then the smallest real run (SC-006) in a separate local data folder and into a copy of `data/truth`: `collect <three article addresses>`, then `truth --limit 3`; keep the terminal output and the seconds of each command; check `local_data/collected/` is empty; record it in research.md and the README.
- [ ] T023 The file list and one commit message to the maintainer, with what was removed and what is not shown yet.
