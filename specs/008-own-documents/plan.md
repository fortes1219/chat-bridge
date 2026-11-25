# Implementation Plan: Asking about your own documents

**Branch**: `dev/rc-0.1.0` (feature directory `specs/008-own-documents/`) | **Date**: 2026-11-25 | **Spec**: [spec.md](spec.md)

## Summary

`chat-bridge ingest <folder> --replace` makes the knowledge base hold the folder's documents and
nothing else, as LangChain's indexing API does with `cleanup="full"`; without the option the
command behaves as before. The sample questions become data that comes with the sample news, and
the service sends them only while the sample news is stored, as open-webui sends its prompt
suggestions from its configuration. The question box's hint and the answering program's
instructions stop naming market news. No package is added.

## Technical Context

**Language/Version**: Python 3.13 (`requires-python = ">=3.11"`); TypeScript 6 on Vue 3.5.

**Primary Dependencies**: none added. research.md `## Packages`.

**Storage**: the knowledge base's existing tables; no table or column is added.

**Testing**: fast tests for the command's option and output, the samples endpoint and the
instructions; slow tests in the container for `--replace` on the real database; page tests for the
sample questions.

**Target Platform**: the same as before: a person's Windows, macOS or Linux machine.

**Performance Goals**: `--replace` reads the stored paths once and removes the others in one
statement; its cost follows the number of stored documents. Every run now reads all stored paths
once, with or without the option, to count the documents not in the folder. `GET /chat/samples` is one indexed query on at most 71 paths.

**Constraints**: the sample news is still ingested when the knowledge base is empty, so a fresh
clone works with one command.

## Constitution Check

| Principle | How this plan meets it |
|---|---|
| I. Ecosystem precedent | No package added; `--replace` follows langchain-core's documented `cleanup` modes and the sample questions follow open-webui's served suggestions, both cited with lines (research.md). |
| II. Clone and run | `uv run chat-bridge` still ingests the sample when the knowledge base is empty. |
| III. Raw documents | Unchanged: the answering program gets retrieved sections, now described as documents. |
| IV. Untrusted content | Unchanged: the person's documents are data, as the sample news was. |
| V. Feature-based | The option lives in `chat_bridge/ingest/`, the sample questions in `chat_bridge/chat/`, the page's part in `views/chat/`. |
| VI. Cost | `--replace` reads the stored paths once and removes in one statement; the samples call is one indexed query. |
| VII. Tests | Fast, slow and page tests for each user story; one real run listed. |
| VIII. Honest claims | The README says what `--replace` removes and when the sample comes back. |
| Frontend standards | Contract first, TanStack Query for the call, Nuxt UI only, both languages. |

## Design

### Service

- `ingest/service.py`: `ingest_folder(root, *, replace=False)`. With `replace`, the stored paths
  are read in full; every stored path that is not one of the folder's readable files is added to
  the documents removed in the same transaction, and listed in a new `IngestReport.not_in_folder`.
  When no file of the folder could be read, nothing is removed and the report says so.
- `ingest/cli.py`: `--replace`; the output lists the removed documents apart from those removed
  for being unreadable; a refused replacement says why and exits with the failure code.
- `chat/samples.py`: reads and checks `data/sample_questions.json` (each question a `Localized`),
  and says whether the knowledge base holds any of the sample news files.
- `chat/router.py`: `GET /chat/samples` → `{"questions": [...]}`, empty when the sample news is not
  stored.
- `chat/answer_prompt.md`, `chat/split_prompt.md`, `strategy/revision_prompt.md`: the first lines and
  the event-date sentence (research.md decision 3).
- `cli.py`, `__init__.py`: the description says a RAG demo over your documents, with sample market
  news.

### Page

- `service/schema/chat.ts`, `service/contract/chat.ts`, `service/api/chat.ts`: the samples call;
  `queries/use-samples-query.ts` and its key.
- `views/chat/components/SampleQuestions.vue`: shows the questions it is given, in the page's
  language, and nothing when there are none; `views/chat/constants.ts` loses the fixed keys.
- `i18n/`: the hint; the `samples` texts are removed.

### Data and docs

- `data/sample_questions.json`: the four questions now in the page's texts.
- `README.md`, `README_tzh.md`: using your own documents (FR-009).

## What it changes elsewhere

As listed in spec.md: 003 FR-014, the answer instructions of 001, and `ingest` of 005.

## Order of work

1. `--replace` and its tests (User Story 1).
2. The sample questions, the hint and the instructions (User Story 2).
3. README, checks, and the commit.
