---
description: "Task list for Codex can answer too"
---

# Tasks: Codex can answer too

**Input**: Design documents from `specs/004-answer-with-codex/`

**Prerequisites**: plan.md, spec.md, research.md (with its `## Packages` table)

**Tests**: The constitution (VII) requires tests with every change in behaviour. Fast tests start
neither program. Tasks marked "Real run" start the maintainer's own Codex, only with consent.

## Phase 1: Shared interface

- [x] T001 `chat_bridge/chat/programs.py`: `Program` (Claude Code, Codex), `Login`, `LoginStatus`, `ProgramError`. `claude_code.py` imports them from here and keeps its names; `ClaudeCodeError` derives from `ProgramError`.

## Phase 2: User Story 1 and 3 - Codex answers, with what an answer needs (P1)

- [x] T002 [US1] [US3] `chat_bridge/chat/codex.py`: find the person's `codex`; start it so it holds to spec FR-004 (no commands, files or going online), each flag cited in research.md; remove its key variables; send the rules, passages and question on standard input; read the JSON events and yield the agent's message when it completes; fail on an `error` or `turn.failed` event, a non-zero exit, no message, or the time limit (FR-004)
- [x] T003 [P] [US1] [US3] Fast tests in `tests/chat/test_codex.py`: the command line holds neither question nor passage; the key variables are removed; a completed message is the answer; each failure rule fails the run on its own

## Phase 3: User Story 2 - Login states and choosing (P1)

- [x] T004 [US2] `codex.login_status()`: `codex login status` with the answer's environment; exit 0 logged in, 1 not logged in, otherwise unknown; no program, not installed (FR-002)
- [x] T005 [US2] `chat_bridge/chat/service.py`: a table from program to module; a named program that is not logged in is refused with its own message; with no name, Claude Code when logged in, else Codex; the record names the program (FR-001, FR-003, FR-005)
- [x] T006 [US2] `chat_bridge/chat/schemas.py` and `router.py`: `ChatRequest.program` is optional; `GET /chat/programs` gives each program's state only (FR-002)
- [x] T007 [P] [US2] Fast tests in `tests/chat/test_programs.py` and `tests/chat/test_codex.py`: exit codes to states; each of the four combinations picks or refuses as US2 says; the state endpoint shows no detail text. `tests/chat/conftest.py` makes Codex look not installed in every chat test, so none reaches the machine's own Codex

**Checkpoint**: every existing test passes unchanged (SC-006).

## Phase 4: Polish and real runs

- [x] T008 [P] `README.md` and `README_tzh.md`: Codex as an answering program, the choice and its default, the login states, what each program runs with, and the recorded attacks (FR-006)
- [x] T009 Checks: ruff, mypy, the fast suite on the host, the slow suite in the container
- [x] T010 Ask the maintainer for consent to T011, in one list
- [x] T011 Real run: the five runs of research.md, with Codex only; keep each response and record (SC-001, SC-003 to SC-005)
- [x] T012 `git ls-files --eol` shows no `w/crlf`; give the maintainer the feature's files with one one-line commit message

## Phase 5: Review follow-ups (2026-11-22, done before the chat page, feature 003)

- [x] T013 `codex._stop`: use the processes `psutil.wait_procs` reports still alive; if any are, the stop fails with a `CodexError` naming them; a process that cannot be killed (`AccessDenied`) is reported the same way, not skipped. Test: a child that survives the kill makes the stop fail
- [x] T014 `codex.login_status`: a `codex` refused because it is in the service's folder is `unknown` with the reason, not `not installed`; only "not found on PATH" is `not installed`. Test both
- [x] T015 `service.answer_stream`: an error that is neither a refusal nor a program error (an `OSError` when starting the program, for one) is recorded with the question before it is raised, for both programs, as feature 001 requires for every question. Test: such an error leaves a record with the error
- [x] T016 `README.md` and `README_tzh.md`: the answer uses the sign-in stored in the person's own program, which is their plan or an API key they saved in that program themselves (`codex login status` exits 0 for both, `codex-rs/cli/src/login.rs:505-520` at `rust-v0.166.0`); keys in the shell are removed. research.md cites the three key variables (`codex-rs/login/src/auth/manager.rs:994-996`)
