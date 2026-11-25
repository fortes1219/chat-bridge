---
description: "Task list for asking about your own documents"
---

# Tasks: Asking about your own documents

**Input**: Design documents from `specs/008-own-documents/`

**Prerequisites**: plan.md, spec.md, research.md (with its `## Packages` and `## Advisories`)

**Tests**: The constitution (VII) requires tests with every change in behaviour.
- Fast tests start no program and reach no network.
- Slow tests run in the container, on the real database, without a model; the whole slow suite runs
  once, on the version delivered.
- Page tests use stand-in API calls.
- Tasks marked "Real run" start the maintainer's own Claude Code or Codex, only with consent.

The feature is one commit, made by the maintainer.

## Phase 1: Replace the sample with my documents (US1; P1)

- [x] T001 `chat_bridge/ingest/service.py`: `ingest_folder(root, *, replace=False)`; with `replace`, every stored document that is not one of the folder's readable files is removed in the same transaction and listed in `IngestReport.not_in_folder`; nothing is removed when no file could be read; without it, the count of stored documents not in the folder (FR-001 to FR-004; research.md decisions 1, 6).
- [x] T002 `chat_bridge/ingest/cli.py`: `--replace`; the removed documents listed apart from the unreadable ones; a refused replacement says why and exits with the failure code; without the option, the line saying how many other documents are stored and what `--replace` does.
- [x] T003 [P] Tests: slow, on the real database: `--replace` removes the other documents and their search entries, removes a file deleted from the folder on the next run, keeps everything when nothing in the folder can be read; without it, the other documents stay (SC-001, SC-002). Fast: the command's option and its output.

## Phase 2: The chat speaks about my documents (US2; P1)

- [x] T004 `chat_bridge/chat/answer_prompt.md`, `split_prompt.md`, `chat_bridge/strategy/revision_prompt.md`, `chat_bridge/cli.py`, `chat_bridge/__init__.py`: no market news named as the knowledge base (FR-006; decision 3); `chat/service.py`: the notice says the documents in the knowledge base (FR-010; decision 5).
- [x] T005 `data/sample_questions.json`; `chat_bridge/chat/samples.py`; `GET /chat/samples` in `router.py`: the questions while the sample news is stored, none otherwise (FR-007; decision 2).
- [x] T006 Page: the samples call in the chat schema, contract and API; `queries/use-samples-query.ts`; `SampleQuestions.vue` shows what it is sent and nothing otherwise; the hint in both languages; the fixed sample texts removed (FR-007, FR-008).
- [x] T007 [P] Tests: fast: the samples file checked, the endpoint with and without the sample news stored, no instruction file naming market news (SC-003, SC-004); page: the questions shown, none shown, the hint in both languages.

## Phase 3: README and delivery

- [x] T008 `README.md`, `README_tzh.md`: using your own documents (FR-009).
- [x] T009 Checks (ruff, mypy, fast suite, the slow suite once in the container, `vue-tsc`, ESLint, Prettier, Vitest), `git ls-files --eol`, OSV and `npm audit`; a person-style run with the service on a copy of the database: replace with `data/documents`, open the page, ask with a stand-in program, read the sources; the file list and one commit message.
- [ ] T010 Real run (consent): one question on the replaced knowledge base with each program, to see the new instructions at work.
