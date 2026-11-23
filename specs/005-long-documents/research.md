# Research: Real long Word and PDF documents

Every need below is met by an installed package that other projects already depend on. Our code
calls the packages and connects them; it adds no conversion or splitting rules of its own.

## Packages

| Need | Package | Version | License | Size | Dependency declared in | Called in |
|---|---|---|---|---|---|---|
| Read a PDF's text layer page by page, with each page's label, without OCR | pypdf | 6.21.2 | BSD-3-Clause | 0.4 MB wheel, pure Python, no dependencies | `open-webui/open-webui@0666e59:pyproject.toml:80` | `open-webui/open-webui@0666e59:backend/open_webui/retrieval/loaders/pdf.py:27`, `:43`, `:46` |
| Read a Word 97 `.doc` as Markdown | office-oxide | 0.1.17 | MIT OR Apache-2.0 | 2.8 MB wheel, no dependencies | `infiniflow/ragflow@91c702e:go.mod:75` | `infiniflow/ragflow@91c702e:internal/deepdoc/parser/office/engine_cgo.go:41` |
| Cut a section's text into passages no longer than the limit, at natural breaks | langchain-text-splitters | 1.1.3 | MIT | 2.7 MB of wheels with the 13 packages it adds (langchain-core, langsmith and smaller ones) | `open-webui/open-webui@0666e59:pyproject.toml:64` | `open-webui/open-webui@0666e59:backend/open_webui/routers/retrieval.py:1497` |
| Count a passage's length in the embedding model's own tokens | transformers (bge-m3's tokenizer, already installed with sentence-transformers) | 5.23.0 | Apache-2.0 | none added | `open-webui/open-webui@0666e59:pyproject.toml:72` | `open-webui/open-webui@0666e59:backend/open_webui/routers/retrieval.py:1376-1377` |

Notes on the citations:

- open-webui's default PDF loader opens the file with pypdf (`loaders/pdf.py:27`), takes the
  page labels (`:43`), and yields one document per page with its text and its `page_label`
  (`:46-53`). RAGFlow's Python parser also uses pypdf
  (`infiniflow/ragflow@8090ffd:deepdoc/parser/pdf_parser.py:36`). open-webui pins 6.21.2; this
  feature pins the same version.
- RAGFlow reads `.doc` through the Go binding of the same office-oxide library, at the same
  version (`OpenFromBytes`, then `ToMarkdown` at `engine_cgo.go:48`). The Python wheel is that
  library's own binding.
- open-webui splits with `RecursiveCharacterTextSplitter` and counts length with a Hugging Face
  tokenizer (`retrieval.py:1497-1500`, `:1367-1377`). langchain's
  `from_huggingface_tokenizer` (`langchain-ai/langchain@8ff3cd3:libs/text-splitters/langchain_text_splitters/base.py:213`)
  does the same with a tokenizer passed in; here it is bge-m3's.

## Decisions

### 1. PDF: pypdf, one section per page

- **Decision**: a PDF is read with pypdf, page by page, as open-webui's default loader reads
  it. Each page with text becomes a section whose heading is its page label (`Page 3`); the
  document is titled by its file name. The page text is kept as plain text and is not parsed as
  Markdown. markitdown keeps reading `.docx`.
- **Rationale**: pypdf is the most used PDF package and the default of the projects followed
  here. A passage does not need a heading from the document: where there is none, the page it
  is on is the place a reader looks it up by, which is what open-webui keeps with each page.
  On the four sample PDFs every search of the spec finds its passage, the spaces inside Chinese
  words are fewest of the readers measured, and it installs as one pure-Python wheel.
- **Why the page text is not parsed as Markdown**: in plain text, a line holding only `-` (a
  chart axis in the central bank file) turns the paragraph above it into a heading; 68 lines of
  chart values became one heading that way. Read as pages, a PDF has no such headings.
- **How much each is used**: PyPI downloads in the last month (pypistats.org, 2026-11-21):
  pypdf 205 million, pdfminer.six 82 million (markitdown's PDF reader), markitdown 19 million,
  docling 4.4 million, pdf-inspector 0.9 million, pdf_oxide 0.2 million. docling is called
  in-process by kotaemon (`Cinnamon/kotaemon@9ad3e4e:libs/kotaemon/kotaemon/loaders/docling_loader.py:47`, `:65`);
  open-webui calls a separate docling server (`backend/open_webui/retrieval/loaders/main.py:247`, `:625`).
  pdf-inspector is private-gpt's first PDF reader (`zylon-ai/private-gpt@2373cc7:private_gpt/components/readers/registry.py:6`).
- **Measured** through the whole ingest and the spec's searches (central bank, AI guidelines,
  Article 70-1 Q&A, ETF Q&A; a search column gives the rank of the passage that answers, within
  the first 8):

  | Reader | Sections | Spaces inside Chinese text | Read time (s) | Added to install | ETF | Article 70-1 | AI guidelines | Central bank | Heading of the passage found |
  |---|---|---|---|---|---|---|---|---|---|
  | pypdf 6.21.2, one section per page (chosen) | 124, 54, 7, 6 pages | 441, 95, 9, 1 | 5.4, 1.1, 0.1, 0.1 | 0.4 MB | 1 | 1 | 1 | 3 | `Page 1`, `Page 1`, `Page 22`, `Page 37` |
  | pypdf 6.21.2, one section per document | 1, 1, 1, 1 | 441, 95, 9, 1 | same | same | 1 | 1 | the whole document | 1 | none |
  | docling 2.151.1, OCR off | 170, 82, 5, 34 headings | 721, 654, 106, 115 | 240, 38, 6.1, 3.7 | about 140 MB of wheels with the CPU build of PyTorch, plus 506 MB of models on first use | 1 | 1 | 1 | 2 | `答：`, —, `說明：`, `Q2：本行不動產選擇性信用管制措施成效為何？` |
  | pdf-inspector 1.27.0 | 147, 28, 6, 23 headings | 1,354, 672, 104, 112 | 10.6, 1.6, 0.1, 0.03 | 6.2 MB | 1 | 1 | 1 | 2 | the question, the title, the chapter, the section |

  With one section per document, a search hit is the whole document: the AI guidelines hit was
  all 36,690 characters, table of contents included. That is why it failed the spec's check, and
  why a PDF is cut by page.
- **Alternatives**:
  - docling, the most used reader that finds headings: finds every ETF question, but reading the
    four files took 288 s against 7 s, after a 0.65 GB download, and its spaces are not fewer.
  - pdf-inspector: finds headings in all four files and is fast, but is used by few projects and
    puts three times as many spaces inside Chinese words.
  - markitdown, the reader until now: one passage per PDF and sentences stored as table rows.
  - pdf_oxide 0.3.78 and kreuzberg 4.10.4: see the lookup on spaces below.

### 2. `.doc`: office-oxide

- **Decision**: `.doc` is read with `office_oxide.to_markdown`.
- **Rationale**: one wheel for Windows, macOS and Linux, nothing else to install. On the
  sample `.doc` it gives the title as a heading and the comparison table as Markdown tables.
- **How much it is used**: 72 thousand PyPI downloads in the last month; version 0.1. No Python
  project was found that depends on the PyPI package; RAGFlow depends on the same library
  through its Go binding (see the table).
- **Alternatives**: open-webui reads `.doc` through unstructured
  (`open-webui/open-webui@0666e59:backend/open_webui/retrieval/loaders/main.py:781`), which
  converts it with LibreOffice; other routes use a Java service or a hosted converter. None of
  them installs as a Python package alone, which "clone and run" needs.

### 3. `.odt`: refused with a reason

- **Decision**: `.odt` is refused with "OpenDocument text is not read; save it as .docx or PDF".
- **Rationale**: the maintainer decided this demo does not read OpenDocument text. Packages that
  read it exist (docling lists ODT among its formats); the refusal says how to convert the file.

### 4. Passages: at most 512 tokens of text, cut by langchain-text-splitters

- **Decision**: before a section's text is embedded, it is split by
  `RecursiveCharacterTextSplitter.from_huggingface_tokenizer(bge-m3's tokenizer, chunk_size=512, chunk_overlap=0)`
  with the separator list langchain documents for languages without word boundaries
  (`langchain-ai/docs@eea3d19:src/oss/integrations/splitters/recursive_text_splitter.mdx:107-134`).
  Each piece carries the section's heading path, which for a PDF is its page. A text of 512
  tokens or fewer is not split. This replaces the token-window split the project wrote itself
  in `chat_bridge/embedding.py`, which cut only beyond 0.9 of bge-m3's 8,192-token window.
- **Rationale**: 512 tokens is RAGFlow's default passage size
  (`infiniflow/ragflow@8090ffd:rag/app/naive.py:1135`, v0.27.3). Splitting where the text is
  embedded leaves the stored sections, and so the 71 sample market files, unchanged: none of
  their sections has more than 512 tokens of text (measured: 0 sections split).
- **How much it is used**: langchain-text-splitters 42 million PyPI downloads in the last month,
  against llama-index-core 5.7 million and semchunk 5.3 million. open-webui depends on it (see
  the table), and so does khoj (`khoj-ai/khoj@ae229ca:pyproject.toml:61`, called in
  `src/khoj/processor/content/text_to_entries.py:72`).
- **Alternatives**: docling's `HybridChunker` splits by document structure and token limit, but
  needs docling's own document model, so every file would go through docling.

### 5. Tables are not split

- **Decision**: Markdown tables stay one passage each, searched by keywords and not embedded,
  as today. The maintainer decided this: a long table is a matter for whoever prepares the
  document.
- **Rationale**: the limit exists because the embedding model reads a bounded text; tables are
  not embedded. None of the packages above splits a Markdown table and repeats its header.
- **Known limits**: a long table is one large passage; the sample `.doc` is two tables of 33
  rows in all. pypdf gives no tables: a PDF's table becomes lines of text in its page, embedded
  with the rest of the page.

### 6. Nothing is removed by rules of our own

- **Decision**: what pypdf takes from a page stays, page numbers, running headers,
  table-of-contents leaders and chart labels included.
- **Rationale**: the constitution allows only package behaviour. What remains is in the defect
  list below.

## Measurements

In the test container (6 cores), on the files in `data/documents/`. Passages are the pieces of
section text after the split.

| Document | Pages | Read in | Passages | Longest passage |
|---|---|---|---|---|
| Central bank press conference material | 124 | 5.4 s | 203 | 512 tokens |
| AI guidelines for the financial industry | 54 | 1.1 s | 64 | 511 tokens |
| Article 70-1 Q&A | 7 | 0.1 s | 9 | 497 tokens |
| ETF Q&A | 6 | 0.1 s | 12 | 505 tokens |
| Life insurance model clauses (`.doc`) | — | — | 0 text passages, 2 tables | — |

The 71 sample market files: 0 sections longer than 512 tokens, so their passages do not change.

After the change, in the container (`tests/ingest/test_long_documents.py`, `tests/search/test_yield.py`):

- every PDF has more than one passage, no passage has more than 512 tokens of text, and every
  section of a PDF is a page;
- the four searches of User Story 1 and a clause of the `.doc` each find their passage among
  the first 8, and the passages found carry their page;
- the `.odt` is refused with its reason, and the other five files are ingested;
- the search-yield suite gives the same numbers as before: 55, 0, 25, 26, 2.

Real run (SC-006), with the maintainer's consent: the five sample files ingested into a fresh
knowledge base on the maintainer's computer, then the ETF Q&A's first question asked once through
`POST /chat/stream`, answered by Claude Code with its tools off:

- the sources shown are the ETF Q&A's pages 1 to 6, then two pages of the central bank file;
- the answer explains what an ETF is and how investors buy and sell one, citing source 1 (page 1)
  for both, and source 2 for creation and redemption in kind; it notes that the document dates
  from 2003;
- the reply took 23 s; ingesting the five files took 307 s with four threads;
- the question and the sections found are kept in the local record, as for every question.

## Conversion defects

Counted on the four sample PDFs: before is markitdown, the reader until now; after is pypdf
page by page. Counts are lines, or places for the spaces. Order of the counts: central bank, AI
guidelines, Article 70-1 Q&A, ETF Q&A.

| Defect | Example after | Before | After | Status |
|---|---|---|---|---|
| A whole PDF is one passage | — | 1, 1, 1, 1 | 203, 64, 9, 12 passages | Fixed |
| Sentences stored as table rows (table rows counted) | — | 1,807, 196, 39, 0 | 0 | Fixed: pypdf makes no tables. A real table becomes text lines |
| No headings | — | none | none; each page is labelled | The page stands in for a heading. A Q&A's questions stay at the start of their answers' text |
| Lone numbers on a line (page numbers, chart values) | `4` | 334, 54, 7, 0 | 881, 53, 7, 0 | Known limit; more in the central bank file, whose charts pypdf reads as text |
| Lines of 1 to 3 characters (chart axis labels) | `4` | 554, 101, 25, 23 | 1,582, 93, 34, 23 | Known limit; as above |
| Table-of-contents leaders | `前言.......` | 0, 9, 0, 0 | 0, 9, 0, 0 | Known limit; the contents page is a section of its own, and the AI guidelines search finds the chapter's page |
| A space where a line broke inside a Chinese word | `服 務` | 706, 18, 0, 1 | 441, 95, 9, 1 | Known limit after the lookup below. Keyword search matched all 128 sections in the sample below |
| Running headers and page numbers inside the page text | — | yes | yes | Known limit |

Spaces are counted as runs: each run of one or more spaces with a Chinese character on both
sides counts once, and neighbouring runs may share a character (`服 務 業` is two).

### The spaces between Chinese characters: what was looked up

Measured on the four PDFs (spaces; ETF and Article 70-1 questions that became headings):

| Reader | Spaces | ETF questions as headings | Article 70-1 questions as headings |
|---|---|---|---|
| markitdown 0.1.9 (before) | 706, 18, 0, 1 | 0 of 17 | 0 of 8 |
| pypdf 6.21.2 (chosen) | 441, 95, 9, 1 | not read as headings | not read as headings |
| docling 2.151.1, OCR off | 721, 654, 106, 115 | 17 of 17 | 2 of 8 |
| pdf-inspector 1.27.0 | 1,354, 672, 104, 112 | 17 of 17 | 4 of 8 |
| pdf_oxide 0.3.78 (MIT or Apache-2.0; `infiniflow/ragflow@91c702e:go.mod:76`, called in `internal/deepdoc/parser/pdf/pdfoxide/pdf_oxide_adapter.go:72`) | 720, 543, 60, 115 | 0 of 17 | 1 of 8 |
| kreuzberg 4.10.4 (MIT; who depends on it was not looked up) | 0, 96, 0, 0 | 0 of 17 | 1 of 8 |

- pdf-inspector's Python call is `process_pdf(path, pages=None)`
  (`firecrawl/pdf-inspector@2e49004:docs/python.md:130`); there is no option for line joins.
- A package that removes spaces between Chinese characters: none found. pangu adds them.

kreuzberg leaves the fewest spaces, but reads no tables and took 1,285 lines of the central bank
file as headings. pypdf leaves the fewest of the others, and no rule of our own removes the rest.

What the spaces cost keyword search, measured with the project's own tokenizer on twelve words
split by a space somewhere in the PDFs (three per PDF, for example 實物買回, 淨資產, 網路平臺,
購屋貸款): of the 128 pages that hold one of the words, all 128 match by keyword as stored. A word
split in one place usually appears unbroken elsewhere on the same page.
