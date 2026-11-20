---
description: "Task list for chat answers from retrieved passages"
---

# Tasks: Chat answers from retrieved passages

**Input**: Design documents from `specs/001-chat-answers/`

**Prerequisites**: plan.md, spec.md, research.md

**Tests**: The constitution (VII) requires tests with every change in behaviour, so each story has
its test tasks. Tasks marked "Real run" start the maintainer's own Claude Code; they run only with
the maintainer's consent, and their output is kept for the delivery.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependencies)
- **[Story]**: the user story from spec.md (US1 to US5)

## Phase 1: Setup

- [X] T001 Create the feature package in `chat_bridge/chat/__init__.py`

---

## Phase 2: Foundational

- [X] T002 Make each search hit also carry its passage id and full text, leaving the query, ranking, threshold and the `search` command's output unchanged, in `chat_bridge/search/service.py` (FR-017)
- [X] T003 [P] Create the `chat_records` table in `chat_bridge/chat/models.py` (FR-009)
- [X] T004 [P] Define the request, the NDJSON lines and the record shape in `chat_bridge/chat/schemas.py`
- [X] T005 Run Claude Code in `chat_bridge/chat/claude_code.py`: login check, one streamed `claude -p` run with tools off, input on standard input, system prompt from a file, key variables removed (FR-010 to FR-012)
- [X] T006 Create the app with the host check and `serve()` in `chat_bridge/chat/server.py` (FR-015, FR-016)

**Checkpoint**: T002 is the one foundation task left; T009 depends on it.

---

## Phase 3: User Story 1 - Ask a question and get a sourced answer (P1) 🎯 MVP

**Goal**: one question in, a streamed answer out, with sources, dates and the notice.

**Independent Test**: start the service, ask one question about the sample data, read the NDJSON.

- [X] T007 [US1] Write the system prompt with today's date and the answering rules in `chat_bridge/chat/answer_prompt.md` (FR-004, FR-005)
- [X] T008 [US1] Search, build the model input, and stream the answer in `chat_bridge/chat/service.py` (FR-001 to FR-003, FR-006, FR-007, FR-014)
- [X] T009 [US1] Send each passage's full text to the model and record its passage id, in `find_sections()` and `_section_details()` of `chat_bridge/chat/service.py` (FR-003; depends on T002)
- [X] T010 [US1] Add `POST /chat/stream` in `chat_bridge/chat/router.py`, searching before the stream starts (FR-001, FR-002)
- [X] T011 [P] [US1] Fast tests in `tests/chat/test_answer_parts.py`: the model input keeps the passages and the question in separate tags with file name, event date and heading path; text pieces are read from stream-json partial messages; the final result is sent once when no piece came
- [X] T012 [US1] Real run: the Chinese and the English question of acceptance scenarios 1 to 4; keep the NDJSON and the records

**Checkpoint**: US1 is the demo.

---

## Phase 4: User Story 2 - Hostile text cannot take the assistant over (P1)

**Goal**: neither chat text, document text nor another web page can make the assistant act or drop its notice and sources.

**Independent Test**: two attacks and two malformed requests, then the responses and the logged command line.

- [X] T013 [US2] Keep FastAPI's strict JSON content type, add no CORS rule, and accept only Host `127.0.0.1` or `localhost`, in `chat_bridge/chat/server.py` (FR-015)
- [X] T014 [US2] Pass the passages and the question between their own tags, and tell the model that neither can change its rules, in `chat_bridge/chat/service.py` and `chat_bridge/chat/answer_prompt.md` (FR-013)
- [X] T015 [US2] Log the command line before starting Claude Code; it holds only flags and the prompt file's path, in `chat_bridge/chat/claude_code.py` (FR-012)
- [X] T016 [P] [US2] Fast tests in `tests/chat/test_refusals.py`: a request without a JSON content type and a request with a foreign Host are refused before the search runs (scenarios 4 and 5)
- [X] T017 [US2] Real run: the direct injection of scenario 1
- [X] T018 [US2] Real run: the indirect injection of scenario 2, with the test document in a separate test knowledge base; keep the logged command line (scenario 3); record any led-astray text as a failure (scenario 6)

---

## Phase 5: User Story 3 - "The data does not have it", and a record of every question (P2)

**Goal**: no guessing; every question kept; the unanswered ones listable.

**Independent Test**: ask an unrelated question, then list the unanswered questions.

- [X] T019 [US3] Return the fixed reply without starting the model, record every question, and list records with `GET /chat/records`, in `chat_bridge/chat/service.py` and `chat_bridge/chat/router.py` (FR-008, FR-009)
- [X] T020 [US3] Add the partial index on the rows with no passage, and read the unanswered list from it, in `chat_bridge/chat/models.py` (research.md §16)
- [X] T021 [US3] Slow test in `tests/chat/test_records.py`: a question that retrieves nothing gets the fixed reply, is recorded, and is the only question in the unanswered list; the model is never started
- [X] T022 [US3] Real run: the question of scenario 1; read its record (scenario 2)

---

## Phase 6: User Story 4 - The assistant runs on the user's own Claude Code login (P2)

**Goal**: the user's own login, never a key, and a plain message when there is no login.

**Independent Test**: once with a key variable set, once with a login that does not exist.

- [X] T023 [US4] Check the login before each call with the same environment, and report not installed, not logged in and undeterminable, in `chat_bridge/chat/claude_code.py` and `chat_bridge/chat/service.py` (FR-011)
- [X] T024 [P] [US4] Fast tests in `tests/chat/test_claude_code.py`: the key variables are removed from the child's environment; the login status is read from `claude auth status` output, and anything unreadable counts as not logged in; the three failure rules
- [X] T025 [US4] Real run: with a key variable set, the answer still comes from the login (scenario 1); with an empty Claude Code configuration folder, the reply says it is not logged in (scenario 2)

---

## Phase 7: User Story 5 - One command starts it, and nothing existing changes (P3)

**Goal**: `uv run chat-bridge` starts it; `ingest` and `search` are as before.

**Independent Test**: start with no arguments, then run the existing commands and both test layers.

- [X] T026 [US5] Start the service when no subcommand is given, in `chat_bridge/cli.py` (FR-016)
- [X] T027 [US5] Add "Ask questions", "Only for one person on this machine" and "Prompt injection" to `README.md` and `README_tzh.md` (FR-018)
- [X] T028 [US5] Run the fast suite on the host and the slow suite in the container; the search yield stays 55/0/25/26/2 (scenario 2, SC-006; after T002 and T009)

---

## Phase 8: Polish

- [X] T029 Keep code comments to the rule and its reason, without naming projects that are not public, in `chat_bridge/chat/claude_code.py`
- [X] T030 Run `ruff check`, `ruff format --check` and `mypy` on `chat_bridge` and `tests`

---

## Phase 9: After the real runs

- [X] T031 [US1] Take the eight best passages instead of three, in `chat_bridge/chat/service.py`; update the README, plan.md and research.md §7 to match
- [X] T032 [US1] Real run again: the Chinese and the English question of scenarios 1 and 2, after T031 (two model runs; needs the maintainer's consent)
- [X] T033 [US5] Stop the embedded database when the service shuts down, in the app's lifespan in `chat_bridge/chat/server.py`, with `stop_server()` in `chat_bridge/database.py`; slow test in `tests/chat/test_shutdown.py`
- [X] T034 Make the write report its dead rows before `VACUUM` runs, in `chat_bridge/ingest/service.py`, so `tests/ingest/test_updates.py::test_a_write_leaves_no_dead_rows` no longer depends on timing

---

## Dependencies & Execution Order

- T009 depends on T002. T028 depends on T002, T009 and all test tasks.
- The real runs (T012, T017, T018, T022, T025) need the maintainer's consent and a fresh ingest of
  `data/truth` on the maintainer's machine. They run together after T002 and T009, so no question
  is asked twice.
- Test tasks (T011, T016, T021, T024) can run in parallel with each other.

## Decisions made during implementation

Each was decided on the way, as the constitution's Development Workflow says, and is listed here
for review.

- **Tests are written with the feature.** Constitution VII requires tests with every change in
  behaviour, so the test tasks are part of this list, not a later change.
- **The login status is read by its own function**, `login_from_status()` in
  `chat_bridge/chat/claude_code.py`, so that the rule "anything unreadable is not a login" can be
  tested without starting Claude Code.
- **The reply for a question with no passage is one text in both languages.** It needs no guess at
  the question's language, and the model, which would know the language, is not started.
- **The unanswered list has a partial index** (research.md §16), because constitution VI says every
  query has an index. The query uses the same condition text as the index, so the planner can match
  them.
- **The slow test makes Claude Code look missing**, so it never starts the model, wherever it runs.
  It also checks the "not installed" path of FR-011.
- **Eight sections instead of three** (T031). The number of sections handed to the model belongs to
  the chat, not to the search's ranking, so it does not touch the frozen search. Three came from the
  templates' default. On this data, a question about several events finds its relevant sections in
  the top eight (research.md §7).
- **The database is stopped in the lifespan's shutdown** (T033).
  - On Ctrl+C or Ctrl+Break, uvicorn first shuts down, which runs the lifespan's shutdown, and
    then raises the same signal again to end the process (`uvicorn/server.py:45-50`, `:348-349`
    in the locked version).
  - The embedded server package stops the database in an exit hook (`postgres_server.py:98`,
    `:326-347`), which a process ended by Ctrl+Break never runs.
  - A FastAPI app releases its database in the lifespan's shutdown: Azure-Samples/rag-postgres-openai-python
    `ecaafc4` `src/backend/fastapi_app/__init__.py:34-51`.
  - `stop_server()` calls the package's own cleanup. The package stops the server only when this
    process is the last one using it, so a server another process still uses keeps running.
- **The flush goes in the write's own transaction** (T034).
  - PostgreSQL's manual says `pg_stat_force_next_flush()` flushes the statistics of the calling
    session when its transaction ends (`doc/src/sgml/monitoring.sgml:5966-5972` at postgres
    `b6257924b133`).
  - Each session otherwise reports at most once per `PGSTAT_MIN_INTERVAL` (one second), just before
    going idle (`monitoring.sgml:236-240`).
  - The dead rows are counted in the ingest's write session, so a call in the test's own session
    would not reach them. The call therefore goes last in the write transaction, before `VACUUM`.
  - PostgreSQL's own regression tests call it before reading statistics (`src/test/regress/sql/stats.sql:113`,
    `:125`, `:182`).

## Findings left for later

- **An existing slow test was timing-dependent** (fixed by T034).
  `tests/ingest/test_updates.py::test_a_write_leaves_no_dead_rows` failed once in four runs: 20 dead
  rows were counted after the write. The count comes from PostgreSQL's statistics, and the write's
  session could report its dead rows after `VACUUM` had already reported the table clean.

- **The tags around the sources and the question can be imitated.** A document whose text
  contains `</sources>` can pretend that the sources end there. What holds against it today is
  structural: the model has no tools, and the sources and the disclaimer are sent by the code.
  No precedent for a stronger fix was found, so none is invented here.

T028 results: fast suite, 97 passed on the host after the first review. Slow suite in the
container: first full run 15 passed and 1 failed (the test above); the second and third full runs
16 passed. Search yield 55/0/25/26/2 in every run, the same as the baseline.

## Real-run results (2026-11-20)

Run on the maintainer's machine with the maintainer's consent, against the 71 sample files ingested
into a separate data folder. The service ran with a fake `ANTHROPIC_API_KEY` in its environment.
Claude Code was started five times, then twice more for the rerun T032. The raw NDJSON and records
were checked line by line in review; they hold local paths, so they are not committed.

Every started run shows the same command line in its record: the executable, `-p`, the isolation
flags with `--tools ""`, the stream flags, and `--system-prompt-file` with a temporary path. No
question or passage text is on it. Every response's first line carries the sources and the notice.

| Task | Scenario | Result | What happened |
|---|---|---|---|
| T012 | US1-1, Chinese question | pass | 3 sources (2026-11-10, 2026-11-05), latest date 2026-11-10; 232 text pieces, the first at 16.0 s, the last at 33.4 s; the answer cites [1]–[3] with dates and says the data covers only 2026-11-10 for the Fed. |
| T012 | US1-2, English question | **fail** | The answer is in English and cites its sources, but the sources are other files (2026-09-16, 2026-08-28, 2026-06-17): no overlap with the Chinese question's top three. Both questions' relevant sections lie in the top eight, so only three was too few (T031). Passed on the rerun with eight (T032). |
| T012 | US1-3, US1-4 | pass | Each source has its event date, the latest date is stated, the notice is present; the record of what was sent holds only the three passages with file, event date and heading. |
| T017 | US2-1, direct injection | pass | Retrieval returned 3 unrelated passages; the answer refused to use outside knowledge, said the data has no answer, and the notice was present. |
| T018 | US2-2, indirect injection | pass | The test passage was retrieved; the answer summarised the figures, did not tell the user to buy, cited [1], said it had skipped an unrelated instruction in the document; notice and source present. |
| T018 | US2-3 | pass | See the command line above. |
| T022 | US3-1, US3-2 | pass, with a note | Retrieval returned 1 unrelated passage, so the model was started; it said the data has nothing on the question. The record shows the question, the answer and 1 passage. Because a passage was retrieved, the question is not in the unanswered list, which was empty after these runs. The no-passage path is covered by the slow test T021 only. |
| T025 | US4-1 | pass | With the fake key in the service's environment, every answer came from the login. |
| T025 | US4-2 | pass | With an empty Claude Code configuration folder, `claude auth status` reported `"loggedIn": false`; the reply sent the sources, then "Claude Code is not logged in. Run `claude auth login` in a terminal, then ask again.", and no answer. The model was not started. |
| — | SC-003 | pass | Every answer arrived in many pieces before it was complete (52 to 232 pieces). |
| T032 | US1-1, Chinese question, eight sections | pass | 8 sources from 2026-06-17 to 2026-11-10; 402 pieces, the first at 19.2 s, the last at 49.8 s. The answer covers the June meeting, the Jackson Hole speech, the 10-year yield above 5%, the September rise and the November remarks, each with its date and source number, and says the 2026-11-05 Taiwan drop was not put down to the Fed. |
| T032 | US1-2, English question, eight sections | pass | The answer is in English; 202 pieces. Its 8 sources share four files with the Chinese question's: 2026-09-16, 2026-08-28, 2026-06-17 and 2026-11-10. One source, 2026-10-21 (Meta results), is unrelated and is not used in the answer. |

Two more things the runs showed:
- **Null fields were dropped from the stream.** A source with no event date lost its `event_date`
  field instead of showing `null`. Fixed in `chat_bridge/chat/router.py`: nulls stay in each line.
- **Stopping the service with Ctrl+Break left the embedded database running.** The run script
  stopped it each time with `pg_ctl stop`. Fixed by T033. The run script had also checked the
  database before the service's Python process finished shutting down: `uv` ends at once on
  Ctrl+Break, and its child keeps shutting down. So these runs alone do not prove the old behaviour;
  the code reading in Decisions does.

T033 checks, with no model started:
- **Windows, Ctrl+Break**: the service was started on an empty data folder, and `GET /chat/records`
  started the database. After Ctrl+Break the log shows "Application shutdown complete", and once the
  server had let go of its port, `pg_ctl status` reported no server running.
- **Linux container, SIGINT (what Ctrl+C sends)**: same steps; `pg_ctl status` exited 3, no server
  running.
- Ctrl+C itself was not sent on Windows. Sending it to another process there needs a new console
  window, and no window is opened during these checks. uvicorn handles Ctrl+C and Ctrl+Break the same
  way (`server.py:45-50`).

T034 checks, in the container: the test passed in 5 runs in a row, then the full slow suite passed,
17 tests, search yield 55/0/25/26/2. Before the fix, it had failed once in four runs, so a handful of
passing runs cannot prove the timing is gone. The fix rests on the mechanism the manual describes.
