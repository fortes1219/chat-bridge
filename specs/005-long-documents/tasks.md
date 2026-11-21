---
description: "Task list for real long Word and PDF documents"
---

# Tasks: Real long Word and PDF documents

**Input**: Design documents from `specs/005-long-documents/`

**Prerequisites**: plan.md, spec.md, research.md (with its `## Packages` table)

**Tests**: The constitution (VII) requires tests with every change in behaviour. Slow tests run
in the Docker container. Only T014 starts Claude Code, with the maintainer's consent.

## Phase 1: Setup

- [x] T001 Add `pypdf==6.21.2`, `office-oxide==0.1.17` and `langchain-text-splitters==1.1.3` with `uv add` (asks the maintainer once)
- [x] T002 [P] [US4] Put the sample originals (four PDFs, one `.doc`) in `data/documents/`, with `docs/sample_documents.md` giving each file's address, publisher, date retrieved and the basis for republishing (FR-009)

## Phase 2: User Story 1 and 2 - read the files, cut the passages (P1)

- [x] T003 [US1] [US2] `chat_bridge/ingest/readers.py`: `.pdf` → pypdf, page by page with each page's label, and `chat_bridge/ingest/sections.py` makes each page a section without parsing it as Markdown; `.doc` → `office_oxide.to_markdown`; `.odt` refused with "OpenDocument text is not read; save it as .docx or PDF" (FR-006, FR-013)
- [x] T004 [US1] `chat_bridge/embedding.py`: `split_for_model` returns the text unchanged when it has 512 bge-m3 tokens or fewer, else the pieces of `RecursiveCharacterTextSplitter.from_huggingface_tokenizer` with the documented separators and no overlap (FR-001, FR-002). The token-window code is removed.
- [x] T005 [US1] `chat_bridge/ingest/service.py`: split a section's text before the heading path is added, so every piece carries it (FR-003)
- [x] T006 [P] [US1] [US2] Fast tests in `tests/ingest/test_readers.py`: each sample PDF becomes one section per page under its page label; the ETF Q&A's first question is on its first page; a PDF without text is refused; the sample `.doc` gives a heading and a table; a small `.odt` is refused with its reason; a mixed folder still names each refusal
- [x] T007 [US1] [US2] Slow test `tests/ingest/test_long_documents.py`: ingest `data/documents/` into a fresh knowledge base; each PDF has more than one passage and no section passage has more than 512 tokens of text (SC-001); each of the four searches of User Story 1 finds its passage in the first 8 (SC-002); a clause of the `.doc` is found in the first 8 (US2-2)

**Checkpoint**: the 71 sample market files give the same passages and the same yield (FR-008).

## Phase 3: User Story 3 and 4 - defects written down, samples shipped (P2)

- [x] T008 [US3] Count each defect kind before (markitdown) and after (pypdf) on the sample PDFs, with an example, into research.md (FR-010)
- [x] T009 [US4] Run the yield suite and the passage count of the 71 sample market files: 316 passages; 55, 0, 25, 26, 2 (SC-004)

## Phase 4: Polish

- [x] T010 [P] `README.md` and `README_tzh.md`: file types read, the `.odt` refusal, the 512-token passages, the known limits, `data/documents/` and its sources
- [x] T011 Checks: ruff and mypy; the fast suite on the host; the slow suite in the container
- [ ] T012 `git ls-files --eol` shows no `w/crlf`; give the maintainer the feature's files with one one-line commit message
- [ ] T013 Ask the maintainer for consent to T014
- [ ] T014 Real run: ask the chat the ETF Q&A's first question; record the sources and the answer (SC-006)

## Dependencies

- T001 before T003 and T004. T002 before T006 and T007.
- T003, T004, T005 before T007. T007 and T009 need the container.
