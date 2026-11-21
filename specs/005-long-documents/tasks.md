---
description: "Task list for real long Word and PDF documents"
---

# Tasks: Real long Word and PDF documents

**Input**: Design documents from `specs/005-long-documents/`

**Prerequisites**: plan.md, spec.md, research.md

**Tests**: The constitution (VII) requires tests with every change in behaviour, so each story has
its test tasks. Slow tests run in the Docker container. Only T021 starts Claude Code, with the
maintainer's consent.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependencies)
- **[Story]**: the user story from spec.md (US1 to US4)

## Phase 1: Setup

- [ ] T001 Add `pypdf==6.21.4` and `office-oxide==0.1.17` to `pyproject.toml` and `uv.lock` with `uv add` (asks the maintainer once)
- [ ] T002 [P] [US4] Put the official originals, the four sample PDFs and the sample `.doc`, in `data/documents/`, with `data/documents/SOURCES.md` giving each file's address, publisher, date retrieved and the basis for republishing (FR-009). The `.odt` files are not shipped.
- [ ] T003 [US2] Save the sample `.doc` as `.docx` with office-oxide into `tests/data/`, named after the `.doc` it comes from (research.md §7)

---

## Phase 2: Foundational

- [ ] T004 Add `count_tokens` to `chat_bridge/embedding.py`: bge-m3's `tokenizer.json` from the pinned model folder, loaded once (research.md §1)
- [ ] T005 In `chat_bridge/ingest/sections.py`, after the heading split, cut each section (FR-001, FR-002; research.md §1–§3):
  - a section with more than 512 tokens of text is split after `\n ! ? ; 。 ； ！ ？`;
  - the pieces are joined in order within 512 tokens;
  - a piece longer than 512 tokens is cut at 512;
  - a table of more than 10 data rows becomes batches of 10, each with the header row and each its own passage;
  - every passage keeps its section's heading path.

  `parse_markdown` takes the counting function; `chat_bridge/ingest/service.py` passes `count_tokens`.
- [ ] T006 [P] Fast tests in `tests/ingest/test_sections.py`, with a stub counter:
  - a short section is unchanged;
  - a long one is cut only after a delimiter and within the limit;
  - a piece with no delimiter is cut at the limit;
  - a 9-row table is unchanged;
  - a 33-row table becomes 4 tables, each with its header.

**Checkpoint**: the 71 sample market files parse to the same 316 passages, byte for byte (FR-008).

---

## Phase 3: User Story 1 - A long PDF is cut into passages that can be found (P1) 🎯 MVP

- [ ] T007 [US1] New `chat_bridge/ingest/pdf.py`, reading with pypdf (research.md §4). Written here, not copied from MaxKB:
  - each page's repeated first and last lines are removed before the pages are joined, by private-gpt's rule: 10 candidate lines, 2 neighbouring pages, digits compared as one, score above 0.5, first header and last footer kept (FR-004);
  - outline → one `##` chapter per entry;
  - else the table of contents' internal links → chapters;
  - else the most common font size is the body, a line more than 2 points larger is `##` and more than 0.5 larger is `###`;
  - in the body text, a line break that does not follow 。 is removed; heading lines are kept (FR-002).

  A PDF with no text is refused as today (no OCR, FR-012).
- [ ] T008 [US1] In `chat_bridge/ingest/readers.py`, read `.pdf` with `pdf.py` instead of markitdown
- [ ] T009 [P] [US1] Fast tests in `tests/ingest/test_pdf.py` on the files in `data/documents/`:
  - the central bank file's chapters follow its outline;
  - the AI guidelines' chapters follow their links;
  - the two Q&As take the font route;
  - no output has Markdown table rows (FR-005);
  - a page number repeated in the same place on neighbouring pages is gone, and the first page keeps its header;
  - no body line is broken mid-sentence; heading lines stay on their own.
- [ ] T010 [US1] Slow test in `tests/ingest/test_long_documents.py`: ingest `data/documents/` into a fresh knowledge base, then check:
  - each PDF has more than one passage and no passage has more than 512 tokens of text (US1-1, SC-001);
  - each of the four spec searches has its passage in the first 8 (US1-2 to US1-5, SC-002);
  - the Article 70-1 answer is found as a sentence (US3-3);
  - a found passage carries its heading where the PDF has one (US1-6, as limited in research.md §9).

---

## Phase 4: User Story 2 - Real Word documents are read, or refused with a reason that helps (P1)

- [ ] T011 [US2] In `chat_bridge/ingest/readers.py`:
  - read `.doc` with `office_oxide.to_markdown`;
  - refuse `.odt` with its own reason: "OpenDocument text is not read; save it as .docx or PDF" (FR-006, FR-007).
- [ ] T012 [P] [US2] Fast tests in `tests/ingest/test_readers.py`:
  - the sample `.doc` gives a heading and a Markdown table;
  - a small `.odt` made by the test is refused with that reason;
  - a folder mixing readable and unreadable files still exits 1 and names each refusal (US2-3).
- [ ] T013 [US2] In the slow test of T010, also check that the `.docx` in `tests/data/` and the `.doc` give passages under the limit, and that a clause from each is found in the first 8 (US2-1, US2-2)

User Story 3's defect list is research.md §9: every defect with an example, its counts before and after, and whether it is fixed (FR-010, SC-005). T018 updates it if the counts change.

---

## Phase 5: User Story 4 - The sample documents ship with the demo (P2)

- [ ] T014 [US4] Run the search-yield suite and the passage count of the 71 sample market files unchanged: 316 passages; 55, 0, 25, 26, 2 (US4-3, SC-004)

---

## Phase 6: Polish

- [ ] T015 [P] `README.md` and `README_tzh.md`:
  - `ingest` reads `.docx`, `.doc`, `.pdf`, `.txt` and `.md`;
  - `.odt` is refused, with what to do;
  - passages are at most 512 tokens of text and long tables are split by 10 rows;
  - the known limits of research.md §9;
  - one sentence saying that a number at the start of a passage or at the end of a source's heading is usually the PDF's page number;
  - `data/documents/` and its source list.
- [ ] T016 [P] Rewrite the docstrings that say sections are split only at headings (`chat_bridge/ingest/sections.py`, `chat_bridge/ingest/service.py`)
- [ ] T017 Checks: ruff and mypy; the fast suite on the host; the slow suite in the container (`docker compose -f compose.test.yml run --rm slow-tests`).
- [ ] T018 Record the before and after numbers here, and update research.md §9 if a count changed (FR-011)
- [ ] T019 `git ls-files --eol` shows no `w/crlf`; give the maintainer every file of this feature with one one-line commit message
- [ ] T020 Ask the maintainer for consent to T021
- [ ] T021 Real run: ask the chat the ETF Q&A's first question; record the sources and the answer (SC-006)

## Dependencies

- T001 before T007 and T011. T004 before T005. T005 before T010.
- T002 and T003 before T009, T010, T012 and T013.
- T006, T009 and T012 can run together.
- T010, T013, T014 and T017 need the container.
