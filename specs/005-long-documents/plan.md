# Implementation Plan: Real long Word and PDF documents

**Branch**: `dev/rc-0.1.0` (feature directory `specs/005-long-documents/`) | **Date**: 2026-11-21 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/005-long-documents/spec.md`

## Summary

`ingest` learns to cut long documents into passages that can be found:

- **PDF**: read with pypdf in three steps.
  - Each page's repeated first and last lines (page numbers, running headers) are removed, as
    private-gpt does.
  - Chapters come from the outline, else from the table of contents' links, else headings come
    from font sizes, as MaxKB does.
  - Lines broken mid-sentence are joined back, by MaxKB's rule.

  markitdown no longer reads PDFs. Every page it judges form-like comes out as Markdown tables,
  which is where sentences became table rows.
- **`.doc`**: read with office-oxide, as RAGFlow does. Nothing else needs installing.
- **`.odt`**: refused, and the report says to save the file as `.docx` or PDF.
- **Every document**: after the heading split, a section with more than 512 tokens of text is
  split after punctuation into passages of at most 512 tokens. A table of more than 10 rows is
  split into batches of 10. Both rules are RAGFlow's.
- **Samples**: the sample long documents ship in `data/documents/` with a source list.

Measured in the container on the seven sample files (numbers in [research.md](research.md)):

- the four PDFs go from 1 passage each to 65, 171, 7 and 9;
- no passage has more than 512 tokens of text;
- no sentence is stored as a table row, and no line is broken mid-sentence;
- page numbers before a chapter title drop from 29 to 9 across the four PDFs;
- the `.doc` becomes 4 passages;
- all six search sentences find their passage among the first 8;
- the 71 sample market files come out unchanged.

What is still wrong, and what each lookup found, is in research.md §9.

**What the maintainer approves with this plan:**

- **Two new dependencies.**
  - `pypdf==6.21.4`: pure Python, 0.4 MB, BSD-3-Clause. It is the version MaxKB pins.
  - `office-oxide==0.1.17`: a 2.5–2.9 MB wheel for Windows, macOS and Linux, MIT or Apache-2.0.
  - Adding them to `pyproject.toml` and `uv.lock` asks for approval once, when that task runs.
- **A change to a settled decision.** Ingest followed "private-gpt and markitdown". For PDFs it
  now follows MaxKB. markitdown still reads `.docx`.

## Technical Context

**Language/Version**: Python 3.13 (`requires-python = ">=3.11"`)

**Primary Dependencies**:
- markitdown 0.1.9 (`.docx`, unchanged);
- pypdf 6.21.4 (new, PDF);
- office-oxide 0.1.17 (new, `.doc`);
- tokenizers, already locked, to count bge-m3 tokens from the model's own `tokenizer.json`.

**Storage**: No schema change. Passages are the existing `sections` rows; a long section simply
becomes several rows with the same heading path.

**Testing**: pytest. Fast tests for the cutting rules and the readers run on the host; the
ingest-and-search tests are marked `slow` and run in the container.

**Target Platform**: The user's own computer: Windows, macOS or Linux.

**Project Type**: A command-line tool that also starts a local web service.

**Performance Goals**: The first ingest of the five sample files into an empty knowledge base
took 230 s in the container (6 cores). Of that:
- reading the files, header and footer step included, took 15.2 s, 11.7 s of it the 124-page file;
- cutting into passages took 0.2 s;
- loading the embedding model took 5.3 s;
- embedding 252 texts took 205.1 s, about 0.8 s each;
- database writes and the rest took 4.4 s.

Embedding was already the slow step; a long document now has many passages to embed instead of
one. Ingesting again with nothing changed took 0.1 s, because unchanged files are skipped. A
search took about 1.1 s, as before: this feature does not touch the search.

**Constraints**:
- no OCR;
- nothing to install beyond Python packages;
- the 71 sample market files ingest and search exactly as before.

**Scale/Scope**: Seven sample files, up to 124 pages; the ingest package only.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | How this plan meets it |
|---|---|
| I. Ecosystem Precedent First | Each rule cites its source with commit and lines (research.md §1–§7). Where the plan differs from its source, the difference and the reason are stated: the tokenizer used for the 512 count, the header repeated in table batches, MaxKB's hard cut instead of RAGFlow's whole piece, and MaxKB's line join applied in the font-size route too. Every known limit lists the projects checked and what they do (§9). |
| II. Clone and Run | Both new packages install from wheels with `uv sync`; no LibreOffice, Java, pandoc or server. `.odt` is refused, not worked around. |
| III. The Model Sees Only Retrieved Passages | Unchanged; passages are now small enough to hand over. |
| IV. Untrusted Content Stays Data | Unchanged. A document is still only text in a passage. |
| V. Feature-Based Structure and Clean Code | Changes stay in `chat_bridge/ingest/`: the reader table gains two entries and a refusal; PDF reading is its own module; the cut is one function beside the heading split. Limits are named constants. |
| VI. Cost Follows the Work | Reading and cutting are linear in the document; unchanged files are still skipped by SHA-256. |
| VII. Tests Prove What the User Gets | Fast tests for each cutting rule and each reader. Slow tests ingest the shipped sample documents and run the six searches. The yield suite runs unchanged. One real chat run for SC-006, with consent. |
| VIII. Honest Claims | The README lists the file types, the `.odt` refusal and the known limits measured in research.md §9. |
| Repository Hygiene | English, LF. The sample files are official texts; their source list gives the legal basis. |

Result: passes.

## Project Structure

### Documentation (this feature)

```text
specs/005-long-documents/
├── spec.md
├── plan.md        # This file
├── research.md    # Measurements and decisions
└── tasks.md
```

### Source Code (repository root)

```text
chat_bridge/
├── embedding.py           # count_tokens: bge-m3's tokenizer, loaded once
└── ingest/
    ├── readers.py         # .pdf -> pdf.py; .doc -> office-oxide; .odt refused with what to do
    ├── pdf.py             # New: page headers and footers out; outline, links or font sizes; lines joined
    ├── sections.py        # New: cap a section at 512 tokens of text; long tables in 10-row batches
    └── service.py         # Passes the token counter to the splitter

data/documents/            # New: the official originals (four PDFs, the .doc) and SOURCES.md

tests/data/                # The .docx saved from the sample .doc, named after it
tests/ingest/              # Fast: the cut, the PDF and .doc readers, the .odt refusal
tests/ingest/test_long_documents.py   # Slow: ingest data/documents, six searches, limits

pyproject.toml, uv.lock    # pypdf, office-oxide
README.md, README_tzh.md   # File types, the passage limit, known limits
```

**Structure Decision**: Reading stays a table from extension to reader (`readers.py`). The cut
belongs to the splitter, after the heading split, so Markdown, Word and PDF all pass through it.
The splitter receives a token-counting function instead of loading the model itself. That keeps
its tests free of the model.

## Complexity Tracking

None.
