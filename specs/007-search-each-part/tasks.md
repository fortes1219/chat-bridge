---
description: "Task list for searching each part of a question before answering"
---

# Tasks: Search each part of a question before answering

**Input**: Design documents from `specs/007-search-each-part/`

**Prerequisites**: plan.md, spec.md, research.md (with its `## Packages` and `## Advisories`)

**Tests**: The constitution (VII) requires tests with every change in behaviour.
- Fast tests start neither program. They use stand-in programs and a search stub.
- Slow tests run in the container, on the real knowledge base, without a model.
- Tasks marked "Real run" start the maintainer's own Claude Code or Codex, only with consent.

## Phase 1: Foundations (all stories need them)

- [x] T001 `chat_bridge/search/service.py`: `search()` takes `candidates` (default 20, so the `search` command is unchanged); `search_many(queries, limit, candidates)` runs several queries in one session with one embedding call; `latest_event_date()` returns `max(documents.event_date)`. `chat_bridge/embedding.py`: `embed_queries()`. `chat_bridge/ingest/models.py`: `Document.event_date` indexed (FR-003, FR-009, FR-012).
- [x] T002 [P] Tests: the chat searches the question for 30 sections from 50 candidates and each part for 8 from 20 (fast, `tests/chat/test_split.py`); `search_many` returns, for each query, what `search()` returns for it (slow, `tests/search/test_multi_part_question.py`); with the default candidates the `search` command is unchanged (the existing slow suite).

## Phase 2: User Story 1 - Each part is searched before the answer (P1)

- [x] T003 [US1] `chat_bridge/chat/split.py` and `split_prompt.md`: `SplitReply`, `SplitOutcome`, `split_question()`, the named limits with their reasons (FR-001, FR-002).
- [x] T004 [US1] `chat_bridge/chat/claude_code.py`: `split_reply()` with `--output-format json --json-schema`, reading `structured_output` (FR-001).
- [x] T005 [US1] `chat_bridge/chat/codex.py`: `split_reply()` with `--output-schema` and the schema file in the run's folder, reading the final agent message as JSON (FR-001).
- [x] T006 [US1] `chat_bridge/chat/service.py`: the four section constants; `find_sections` at 30 from 50; `gather_sections`; `answer_stream` runs the split after choosing the program and before the context; the program table gains `split_reply`; the record gains `split` and `searches` (FR-003, FR-004, FR-007, FR-010).
- [x] T007 [P] [US1] Fast tests in `tests/chat/test_answer_parts.py`: the question's sections come first in rank order, then each part's in listed order; a section found twice keeps its first number; nothing is cut; the record holds each search's sections and numbers; a question the search finds nothing for gets the fixed answer and no split run.
- [x] T008 [P] [US1] Fast tests in `tests/chat/test_claude_code.py` and `test_codex.py`: the split command lines hold the schema and the isolation arguments, and not the question; two stand-ins, an executable and a `.cmd` launcher on Windows, started as the split starts Claude Code, receive the schema argument unchanged; the split run is stopped when the client stops reading, as the answer run is.
- [x] T009 [US1] `tests/data/multi_part_question.json` and slow test `tests/search/test_multi_part_question.py`: research.md decision 12, with the parts split from the question's own wording; the `search` command's output for the existing test queries is unchanged (SC-002, SC-006).

## Phase 3: User Stories 2 and 3 - A failed split is said; the parts stay search text (P1)

- [x] T010 [US2] [US3] `chat_bridge/chat/schemas.py` and `service.py`: `ChatContext.split_failed`; a failed outcome continues with the question's own sections and sets it (FR-005, FR-006).
- [x] T011 [P] [US2] [US3] Fast tests in `tests/chat/test_split.py`: program error, time limit, no structured output, invalid JSON, an extra field, an empty part, a part over 200 characters each give a failed outcome and `split_failed` in the context; more than 8 parts are trimmed and counted; duplicates and a part equal to the question are searched once; an empty list is not a failure; a part holding SQL or prompt text reaches the search stub only as its query argument and appears nowhere in what the answer run is given (SC-003).

## Phase 4: User Story 4 - Honest about what the data covers (P2)

- [x] T012 [US4] `chat_bridge/chat/answer_prompt.md`: research.md decisions 8 and 11. `chat_bridge/chat/service.py`: the context's date from `latest_event_date()` (FR-008, FR-009).
- [x] T013 [P] [US4] Fast tests: the instructions no longer tell the model to say the data has nothing, and carry the per-part and market-table wording; the context's date is the knowledge base's latest, not the sources' (SC-005).

## Phase 5: Page

- [x] T014 `frontend/src/service/schema/chat.ts`, `frontend/src/views/chat/components/SourceList.vue`, `frontend/src/i18n/{en,zh-TW}.ts`: `split_failed` in the context schema; the failed-split line; the date labelled as the data's. The line "Searching the news…" already shows until the context arrives (FR-011).
- [x] T015 [P] `frontend/tests/views/chat/chat.spec.ts`: the date label and the failed-split line in both languages; before the context the page says the news is being searched and shows no program's waiting line, and the stop button stops the answer; a context without `split_failed` is refused by the schema.

- [x] T021 `AnswerContent.vue`, `SourceList.vue`, `useCitedSources.ts`, both i18n files: the count above the answer with the whole list behind it, the cited sources under the answer, the line for an answer that cites none (FR-013). Page tests: 60 sources, a date in brackets and a number no source has are not cited, an answer that cites none; the hostile-content check covers the opened list. Looked at in headless Edge with a stand-in `claude` (research.md decision 13).

- [x] T022 FR-014: `left_out_heading` in `search()` and `search_many()`, `sections_headed()`, `MARKET_SECTION` passed by the chat, the market sections appended after the searched sections (research.md decision 14).
- [x] T023 Fast tests: the question's and the parts' searches leave the market section out; each document's market section comes last, numbered on, once. Slow test: replaying the parts each program listed, every market section comes after the searched sections and belongs to a document found by them.

- [x] T024 The question's search as before this feature, 8 sections from 20 candidates with every section ranking, kept whole and first (FR-003, FR-004). Fast test: both searches and the order. Slow test: today's 8 come first, whole, in order, for every replayed set of parts. Replayed the 26 cases and the market-number questions (research.md decision 14).

## Phase 6: Checks and real runs

- [ ] T016 Run the fast suite, `ruff`, `mypy`, the page tests and type check, and the slow suite in the container; check `git ls-files --eol` shows no `w/crlf`.
- [x] T017 Start the service with `uv run chat-bridge` as a person would: the page loads, and a question the data has nothing on still gets the fixed answer without starting a program. Any question that starts a program is a real run (T018).
- [x] T018 Real run (consent, 2026-11-23; results in research.md "Results"; the English runs fail the 0050 part, open): the runs listed in research.md "Real runs", each recorded with the times of SC-007; save the parts each program listed to `tests/data/multi_part_question.json` and run T009's test with them (SC-001, SC-002, SC-004, SC-007).
- [x] T019 README (both languages): what the split does, what the measurement and the tests show, what only the real runs show, and the open gap of spec Assumptions.
- [ ] T020 Hand over the file list and a one-line commit message.
