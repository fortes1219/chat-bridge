# Implementation Plan: Chat answers from retrieved passages

**Branch**: `dev/rc-0.1.0` (feature directory `specs/001-chat-answers/`) | **Date**: 2026-11-20 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/001-chat-answers/spec.md`

## Summary

A local chat service answers a question from the knowledge base. It searches with the question as
asked, takes the eight best passages, and sends them with the question to the user's own logged-in
Claude Code. Claude Code runs with every tool turned off.

The answer streams back as NDJSON: first a context line with the sources and a fixed notice, both
built by the code, then the answer in pieces as the model writes it.

A question that retrieves nothing gets a fixed reply without starting the model. Every question is
recorded, so the questions the data cannot answer can be listed.

The flow is the Azure rag-postgres template's simple flow; the model call follows Vibe-Trading and
the Claude Agent SDK. The decisions and their sources are in [research.md](research.md).

## Technical Context

**Language/Version**: Python 3.13 (`requires-python = ">=3.11"`)

**Primary Dependencies**:
- FastAPI 0.163.2, with Starlette 1.10.0 and Uvicorn 0.54.0, all already in `uv.lock`;
- SQLAlchemy (async) with asyncpg;
- pixeltable-pgserver 0.7.2;
- sentence-transformers with bge-m3;
- the user's own Claude Code CLI.

No new dependency.

**Storage**: The embedded PostgreSQL in `local_data/pgdata`. One new table, `chat_records`, with a
partial index for the unanswered list.

**Testing**: pytest. The fast layer runs on the host; the layer marked `slow` runs in the Docker
container. ruff and mypy (strict) with the FastAPI repository's settings.

**Target Platform**: The user's own computer: Windows, macOS or Linux.

**Project Type**: A command-line tool that also starts a local web service.

**Performance Goals**: The answer starts streaming as soon as Claude Code writes. The first question
after a start also waits for the embedding model to load.

**Constraints**:
- the service listens on 127.0.0.1 only;
- no API key is used;
- Claude Code runs with no tools;
- one answer may take at most 600 seconds.

**Scale/Scope**: One user; the 71 sample files.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | How this plan meets it |
|---|---|
| I. Ecosystem Precedent First | Each approach cites a precedent in [research.md](research.md) (16 decisions). None is marked as having no precedent. |
| II. Clone and Run | `uv run chat-bridge` starts the service (FR-016). The model is the reader's own Claude Code; no key is read (FR-010). |
| III. The Model Sees Only Retrieved Passages | The model gets the eight passages the hybrid search returns, with file name, event date and heading path (FR-003). The search already refuses an index built with another embedding model. |
| IV. Untrusted Content Stays Data | Tools off. The question and the passages go in on standard input, between labelled tags. The notice and the source list are attached by code (FR-007, FR-012 to FR-014). |
| V. Feature-Based Structure and Clean Code | One package, `chat_bridge/chat/`, with its own models, schemas, service and router, as `ingest/` and `search/` are. Unreadable lines of Claude Code's output are skipped, not refused: they are not messages, and the final result line decides success or failure. |
| VI. Cost Follows the Work | Both record lists take a limit of 1 to 10,000 and read the newest rows from an index: the primary key, or a partial index on the unanswered rows (research.md §16). A question costs one search and at most one model run. |
| VII. Tests Prove What the User Gets | Fast tests for the refused requests and for what reaches the model. A slow test for the unanswered path, which needs no model. The real runs that call Claude Code are recorded and delivered (tasks T012, T017, T018, T022, T025). |
| VIII. Honest Claims | Each answer states the latest date its sources reach, says when the data holds no answer, and carries the fixed notice. The README says no wording fully prevents prompt injection. |
| Repository Hygiene | English, LF; no machine details or secrets; the containers are unchanged. |

Result: passes. Re-checked after the design: no change.

## Project Structure

### Documentation (this feature)

```text
specs/001-chat-answers/
├── spec.md
├── plan.md        # This file
├── research.md    # Decisions and their sources
└── tasks.md
```

### Source Code (repository root)

```text
chat_bridge/
├── cli.py                 # No subcommand: starts the chat service
├── chat/                  # This feature
│   ├── __init__.py
│   ├── answer_prompt.md   # The system prompt
│   ├── claude_code.py     # Login check and one streamed `claude -p` run
│   ├── models.py          # chat_records and its partial index
│   ├── router.py          # POST /chat/stream, GET /chat/records
│   ├── schemas.py         # The request, the NDJSON lines, a record
│   ├── server.py          # The app, its host check, and serve()
│   └── service.py         # Search, answer stream, recording, listing
└── search/
    └── service.py         # Each hit also carries its passage's id and full text

tests/
└── chat/                  # Fast tests, and one slow test for the unanswered path

README.md, README_tzh.md   # "Ask questions"; one person on this machine; prompt injection
```

**Structure Decision**: The chat is one feature package, as `ingest/` and `search/` are, each with
its own models, service and entry points. The search changes only by carrying two more fields on
each hit; its query, ranking and threshold stay as they are (FR-017).

## Complexity Tracking

None.
