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
- [x] T013 Ask the maintainer for consent, then the smallest real run (SC-003) through `uv run chat-bridge collect <one article address> --into <a copy of data/truth>`; keep the terminal output and the seconds, set the file beside an earlier one section by section, record it in research.md and the README's time and cost.
- [ ] T014 The file list and one commit message to the maintainer, saying what feature 013's collected pages and feature 015's ingest became.
