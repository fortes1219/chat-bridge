---
description: "Task list for the collect command"
---

# Tasks: Collect new knowledge with a command

**Input**: Design documents from `specs/013-collect/`

**Prerequisites**: plan.md, spec.md, research.md (with its `## Packages` and `## Advisories`)

**Tests**: Fast tests use saved pages, a saved feed and stand-in closes, and reach no network. The real
run reads a few public pages, a feed, Yahoo and FinMind once.

One commit the maintainer makes, after the checks.

- [x] T001 Dependencies: trafilatura, feedparser and ruamel.yaml at the research.md versions (asks for approval); OSV check of `uv.lock`.
- [x] T002 `chat_bridge/collect/pages.py`: robots.txt, spacing, User-Agent, no insecure retry; page or feed; the main text and metadata; the file's name and front matter; unchanged pages left alone (FR-001 to FR-004).
- [x] T003 `data/market_series.json` and `chat_bridge/collect/markets.py`: the markets and series as data; day 0 from `event_time` and by the date rule; `event_time` checked against `event_date` (FR-005, FR-006).
- [x] T004 `chat_bridge/collect/closes.py` and `chat_bridge/strategy/taiwan_sources.py`: the series for a span, each read once a run; placeholder bars and sessions not ended left out; missing days from the second source (FR-007).
- [x] T005 `chat_bridge/collect/moves.py`, `news_files.py` and `service.py`: the rows, notes and first line; the section placed or replaced and the data sources, written only when the cells or notes change (FR-007, FR-008).
- [x] T006 `chat_bridge/collect/cli.py`: the subcommand, the report of what was collected, left alone or refused and why, the exit code.
- [x] T007 [P] Tests: each scenario of spec User Stories 1 to 5; SC-001, SC-002, SC-003 and SC-005; a collected file and a file with `event_time` read by the ingest parser.
- [x] T008 `docs/truth_format.md` sections 1 and 7, `README.md`, `README_tzh.md` (FR-009, User Story 6).
- [x] T009 Run as a person (SC-006): in a copy of the knowledge base, collect one public page and one public feed, ingest them, find them with `search`; SC-004 on the earlier news files; keep the terminal output and record the results in research.md.
- [x] T010 Checks (ruff, ruff format, mypy, fast suite), `git ls-files --eol`; the file list and one commit message to the maintainer.
