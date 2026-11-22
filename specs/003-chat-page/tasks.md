---
description: "Task list for A chat page in the browser"
---

# Tasks: A chat page in the browser

**Input**: Design documents from `specs/003-chat-page/`

**Prerequisites**: plan.md, spec.md, research.md (with its `## Packages` table)

**Tests**: The constitution (VII) requires tests with every change in behaviour. Tasks marked
"Real run" use the maintainer's own Claude Code or Codex, only with consent.

## Phase 0: Feature 004 follow-ups first

- [x] T001 Do feature 004's tasks T013 to T016 (its review follow-ups) and their tests, before the page shows login states.

## Phase 1: The service side

- [x] T002 `chat_bridge/chat/router.py`: `/chat/stream` answers through `fastapi.sse.EventSourceResponse`; each context and piece is one unnamed event; an error after the start is one `error` event with `{"message": ...}`; what the endpoint accepts and refuses is unchanged (FR-002, FR-009)
- [x] T003 [P] Fast tests in `tests/chat/test_stream_events.py`: the event lines for a context, two pieces and an error; the refusal tests pass unchanged (SC-006)
- [x] T004 `chat_bridge/web.py` and `cli.py`: check Node.js and name it when missing or older than the latest security release of a supported line (research.md, ## Advisories), with the version to install; run `npm run build` in `frontend/` when the built page is missing or its sources changed, and `npm install --ignore-scripts` before it when `node_modules` is missing or the lock file changed; serve `frontend/dist` at `/` with unknown paths answered by `index.html` (FR-001, FR-008)
- [x] T005 [P] Fast tests in `tests/web/test_web.py`: Node.js missing or too old is reported by name; a build is skipped when nothing changed and run when a source changed; `/` and an unknown path return the page; `/chat/*` still reaches the service

## Phase 2: The page's data layer (research.md decision 0)

- [x] T006 `frontend/` scaffold from the packages of research.md: Vite, Vue, Nuxt UI, vue-router, vue-i18n, TanStack Vue Query, ESLint, Prettier, Vitest with happy-dom; `package-lock.json` committed, and `npm audit` reports no advisory in it (research.md, ## Advisories), except the five test-only ones the maintainer chose to keep there; `frontend/dist` and `frontend/node_modules` git-ignored
- [x] T007 `service/schema/` (`.strict()` zod for programs, chat context and pieces, the error body), `service/contract/` (the oRPC routes `programs` and `ask`, types only), `service/error.ts` (`AppError`, normalisation, `parseContract`), `service/request.ts` (one axios instance with the fetch adapter for JSON and for the stream with `responseType: 'stream'` read through `EventSourceParserStream`, no client timeout on the stream, signal passed through, cancellation rethrown)
- [x] T008 `service/api/programs.ts` and `service/api/chat.ts`: each checks its input, calls `request`, and parses the 2xx response or each streamed event with its schema; an `error` event becomes an `AppError`
- [x] T009 `queries/`: key factory, shared client (retry network and 5xx twice, no refetch on focus or reconnect, mutations not retried), `use-programs-query`, `use-ask-mutation`
- [x] T010 [P] Tests in `frontend/tests/service/` and `frontend/tests/queries/`: each API function's URL, method and parsed result; a response or event that does not match its schema is a `contract_error` and is never returned; the error normalisation; the retry rule; the queries return the API functions' data

## Phase 3: User Story 0 - Log in first (P1)

- [x] T011 [US0] `views/chat/components/LoginGate.vue`: read the login states before drawing anything; with neither logged in, the empty state lists each program's state and next step, copyable login commands and a check-again button with a spinner; a failed read shows "the service cannot be reached" with the same button (FR-011, US0-1 to US0-8)
- [x] T012 [P] [US0] View tests: each of the four states, the button refetching, a failed read, and no chat or strategy drawn without a login (SC-007)

## Phase 4: User Story 1 and 2 - Ask and read safely (P1)

- [x] T013 [US1] `views/chat/`: `ChatPage.vue` with `ChatPanel` (`UChatMessages`, `UChatPrompt`), `SourceList` (number, file, heading, event date), the latest date and the notice, stop, `SampleQuestions` that fill the box; `useAsk` reads the stream and stops it; `useAddressState` keeps the language and the program in the address (FR-002 to FR-004, FR-010, FR-012, FR-014)
- [x] T014 [US2] Answers rendered by `@comark/vue` with its security plugin as research.md decision 2 sets it; sources as plain text (FR-005)
- [x] T015 [P] [US2] View tests with the hostile text of User Story 2: no script, iframe, object, embed, link or style element; no handler; no `javascript:` or `data:` link; no image with an outside or data address in the rendered page (SC-003)

## Phase 5: User Story 3 to 5 and the layout (P2)

- [ ] T016 [US3] A message for each condition of FR-006; logged out after opening returns to the login screen
- [ ] T017 [US4] `i18n/` for every page text in `zh-TW` and `en`, at most three key levels; the language in the address (FR-007, SC-004)
- [ ] T018 Layout: chat as the main panel, a resizable `StrategyPlace` saying it comes later, a drawer in a narrow window (FR-013)
- [ ] T019 [P] View tests for the messages of US3, the language switch and the layout's drawer

## Phase 6: Polish and real runs

- [ ] T020 [P] `README.md` and `README_tzh.md`: the page's address, the login screen, the stream as Server-Sent Events
- [ ] T021 Checks: ruff, mypy, the fast suite, the slow suite in the container; in `frontend/`: `vue-tsc`, ESLint, Prettier check, Vitest; advisories: `npm audit` for `package-lock.json` and an OSV check of `uv.lock` show none
- [ ] T022 Ask the maintainer for consent to the real runs of research.md, in one list
- [ ] T023 Real run: the runs of research.md; keep what the page showed
- [ ] T024 `git ls-files --eol` shows no `w/crlf`; give the maintainer the feature's files with one one-line commit message
