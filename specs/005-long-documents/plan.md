# Implementation Plan: Real long Word and PDF documents

**Branch**: `dev/rc-0.1.0` (feature directory `specs/005-long-documents/`) | **Date**: 2026-11-21 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/005-long-documents/spec.md`

## Summary

`ingest` reads real long documents with installed packages and cuts them into passages that can
be found. Our code only calls the packages and connects them.

- **PDF**: read with pypdf page by page, as open-webui's default loader reads it. Each page is
  a section under its page label; the page text is not parsed as Markdown. markitdown no longer
  reads PDFs.
- **`.doc`**: read with office-oxide.
- **`.odt`**: refused, and the report says to save the file as `.docx` or PDF.
- **Passages**: where a section's text is embedded, langchain-text-splitters cuts it into pieces
  of at most 512 bge-m3 tokens, at the separators langchain documents for Chinese. Each piece
  carries the section's heading path. This replaces the token-window split written in
  `chat_bridge/embedding.py`.
- **Samples**: the sample long documents ship in `data/documents/` with a source list.

Measured in the container (numbers in [research.md](research.md)):

- the four PDFs give 203, 64, 9 and 12 passages, none longer than 512 tokens;
- every search of the spec finds its passage among the first 3, labelled with its page;
- the 71 sample market files have no section longer than 512 tokens, so their passages do not
  change.

**What the maintainer approves with this plan:**

- **Three new dependencies**, each listed with a project that depends on it in research.md:
  `pypdf==6.21.2` (0.4 MB, BSD-3-Clause), `office-oxide==0.1.17` (2.8 MB, MIT or Apache-2.0),
  `langchain-text-splitters==1.1.3` (2.7 MB with the 13 packages it brings, MIT). Adding them
  asks for approval once.
- **One dependency narrowed**: markitdown no longer reads PDFs, so its `pdf` extra is dropped
  (`markitdown[docx]`). That removes pdfminer.six, pdfplumber, pypdfium2 and four packages only
  they used. Re-resolving moved soupsieve from 4.1.2 to 4.1.3.
- **Known limits**, listed in research.md with counts: long tables stay one passage; text the
  PDF reader keeps (page numbers, chart labels, contents leaders, a space where a line broke
  inside a Chinese word) stays.

## Technical Context

**Language/Version**: Python 3.13 (`requires-python = ">=3.11"`)

**Primary Dependencies**: pypdf (PDF), office-oxide (`.doc`), markitdown (`.docx`,
unchanged), langchain-text-splitters (passages), bge-m3's tokenizer through sentence-transformers
(already installed).

**Storage**: No schema change. Sections are stored as today; a long section gives several search
entries, one per piece, as the token-window split already did for texts over 7,372 tokens.

**Testing**: pytest. Fast tests for the readers on the shipped sample files; slow tests in the
container for the split, the six searches and the yield suite.

**Target Platform**: The user's own computer: Windows, macOS or Linux. All three packages ship
wheels for the three.

**Project Type**: A command-line tool that also starts a local web service.

**Performance Goals**: Reading the 124-page PDF took 10.0 s in the container; the other three
under 2 s. Embedding the passages stays the slow step, as before.

**Constraints**: No OCR. Nothing to install beyond Python packages. The 71 sample market files
ingest and search exactly as before.

**Scale/Scope**: Five sample files, up to 124 pages; `chat_bridge/ingest/` and the split in
`chat_bridge/embedding.py`.

## Constitution Check

| Principle | How this plan meets it |
|---|---|
| I. Ecosystem Precedent First | Every need is a package in the `## Packages` table, cited with the project that depends on it and calls it. The two values passed to the splitter (512 tokens, the separators) cite their sources. No conversion or splitting rule of our own. |
| II. Clone and Run | All three packages install from wheels with `uv sync`; no LibreOffice, Java or pandoc. |
| III. The Model Sees Only Retrieved Passages | Unchanged; passages are now small enough to hand over. |
| IV. Untrusted Content Stays Data | Unchanged. A document is still only text in a passage. |
| V. Feature-Based Structure and Clean Code | The reader table gains two entries and a refusal; the split keeps its place in `embedding.py`, now a call to the package. The hand-written token windows are removed. |
| VI. Cost Follows the Work | Reading and splitting are linear in the document; unchanged files are still skipped by SHA-256. |
| VII. Tests Prove What the User Gets | Fast tests read the shipped files; slow tests ingest them and run the searches; the yield suite runs unchanged. One real chat run, with consent. |
| VIII. Honest Claims | The README lists the file types, the `.odt` refusal and the known limits. |

Result: passes.

## Project Structure

```text
chat_bridge/
├── embedding.py           # split_for_model: langchain-text-splitters with bge-m3's tokenizer, 512 tokens
└── ingest/
    ├── readers.py         # .pdf -> pypdf pages; .doc -> office-oxide; .odt refused with what to do
    ├── sections.py        # read_document: a PDF's pages become sections under their labels
    └── service.py         # each piece of a section's text carries the heading path

data/documents/            # the sample originals (four PDFs, one .doc)
docs/sample_documents.md   # each file's source, publisher, date and basis for republishing

tests/ingest/test_readers.py          # fast: the readers on the sample files, the .odt refusal
tests/ingest/test_long_documents.py   # slow: ingest data/documents, passage limit, searches

pyproject.toml, uv.lock    # the three packages
README.md, README_tzh.md   # file types, the passage limit, known limits
```

**Structure Decision**: reading stays a table from extension to reader. The split stays where
text meets the model, so stored sections, and every search entry of a short section, are
exactly as before.

## Complexity Tracking

None.
