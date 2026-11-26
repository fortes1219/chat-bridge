---
description: "Task list for collecting from the channels"
---

# Tasks: Collect from the channels with the person's own agent

**Input**: Design documents from `specs/015-collect-channels/`

**Prerequisites**: plan.md, spec.md, research.md (with its `## Packages` and `## Advisories`)

**Tests**: Fast tests use a stand-in agent and stand-in pages, and reach no network and start no
program. The run as a person starts the person's own Claude Code or Codex, only with their consent.

One commit the maintainer makes, after the checks.

- [x] T001 `data/channels.json` and `chat_bridge/collect/channels.py`: the channel list read and checked (FR-001).
- [x] T002 `chat_bridge/chat/claude_code.py`, `codex.py`: a shaped reply with the given web tools; the chat's own runs unchanged (User Story 2).
- [x] T003 `chat_bridge/collect/channels_prompt.md` and `channels.py`: the question with the channels and the start date; the answer read, pages off the channels' sites refused (FR-003 to FR-005).
- [x] T004 `chat_bridge/collect/cli.py`: no address and no path collects from the channels; web collecting ends with an ingest of the folder; news files are not ingested; the progress lines (FR-002, User Story 1).
- [x] T005 [P] Tests: each scenario of User Story 1 with a stand-in agent; the command line of each program (SC-001, SC-002).
- [x] T006 `README.md`, `README_tzh.md` (FR-006).
- [x] T007 Ask the maintainer for consent, then the smallest real run (SC-003): one channel, one page the agent names, collected and ingested once into a separate local data folder, and a question that finds it; keep the terminal output and record it in research.md.
- [x] T008 Checks (ruff, ruff format, mypy, fast suite), `git ls-files --eol`; the file list and one commit message to the maintainer.
