# Research: Real long Word and PDF documents

**Result first.** Five precedents together make real long documents work:

- PDFs are read the way MaxKB reads them (outline, then internal links, then font size), with pypdf.
- Each page's repeated first and last lines (page numbers, running headers) are removed before
  the pages are joined, the way private-gpt does.
- Lines broken mid-sentence are joined back, by MaxKB's rule.
- `.doc` is read with office-oxide, as RAGFlow does.
- Every passage is capped at 512 tokens of text, cut after punctuation, and a table of more than
  10 rows is cut into batches of 10. Both rules are RAGFlow's.

Measured on the seven sample files:

- each PDF becomes many passages;
- no passage holds more than 512 tokens of text;
- no sentence is stored as a table row;
- no line is broken mid-sentence;
- the `.doc` is read;
- the 71 sample market files come out byte for byte the same;
- all six search sentences find their passage in the first 8.

What is still wrong is in §9, the defect list. Each item there says which projects were checked
and what they do; none of them fixes it without a model.

Every number was measured in the test container, with the committed code. The variants replaced
the reader and the splitter in memory only. Versions: pypdf 6.21.4 (the version MaxKB pins,
`pyproject.toml:57`) and office-oxide 0.1.17. Line numbers refer to the commit given.

## Measurements

Passages are counted after the heading split and the cap. Tokens are bge-m3 tokens of the text
outside tables. "Table rows" are Markdown table lines in the passages.

| File | Today | With this plan |
|---|---|---|
| AI guidelines, PDF, 54 pages | 1 passage; 13,007 tokens; 337 table rows | 65 passages (36 headings, from the internal links); max 509 tokens; 0 table rows |
| Central bank material, PDF, 124 pages | 1 passage; 52,528 tokens; 2,705 table rows | 171 passages (53 headings, from the outline); max 512 tokens; 0 table rows |
| Article 70-1 Q&A, PDF, 7 pages | 1 passage; 1,398 tokens; 53 table rows | 7 passages (font sizes); max 499 tokens; 0 table rows |
| ETF Q&A, PDF, 6 pages | 1 passage; 4,263 tokens | 9 passages (font sizes); max 495 tokens |
| Life insurance model clauses, `.doc` | refused: unsupported file type | 4 passages: one table of 33 rows in batches of 10 |
| Two amendment tables, `.odt` | refused: unsupported file type | refused, with what to do (§6) |
| 71 sample market files | 316 passages | 316 passages, 0 files changed |

Searches with a limit of 8, on a fresh knowledge base holding the four PDFs and the `.doc`:

| Search | Expected passage | Rank |
|---|---|---|
| 何謂指數股票型基金？投資人如何買賣指數股票型基金？ | ETF Q&A, question 1 with its answer | 1 |
| 本法第70條之1規範之對象包括哪些? | Article 70-1 Q&A, question 1 with its answer | 1 |
| 落實透明性與可解釋性 | AI guidelines, chapter 5, not the table of contents | 1 (ranks 2, 3, 7 and 8 are chapter 5 too) |
| 第2戶購屋貸款成數 | Central bank file, the passage stating the limit of 6 tenths | 4 (ranks 1 and 2 are chart labels, §9; rank 3 is the same chapter's answer on lending) |
| 本契約的解釋，應探求契約當事人的真意 | `.doc`, article 1 | 3 (keyword only, §9) |
| 被保險人故意自殺 保險人不負給付保險金的責任 | `.doc`, a batch of clauses | 1 (keyword only) |

**Time.** These are the numbers from the first ingest of these five files into an empty
knowledge base, in the container (6 cores, 8 GB):

| Step | Time |
|---|---|
| Ingest in total | 230 s |
| Reading the files, including the header and footer step | 15.2 s (central bank 11.7 s, AI guidelines 3.4 s, the rest under 1 s) |
| Cutting into passages | 0.2 s |
| Loading the embedding model | 5.3 s |
| Embedding 252 texts | 205.1 s, about 0.8 s each |
| Database writes and the rest | 4.4 s |

- A second ingest with nothing changed took 0.1 s: unchanged files are skipped by their SHA-256.
- A search took about 1.1 s, the same as before; this feature does not touch the search.
- Embedding was already the slow step before this feature. What is new is that a long document
  now has many passages to embed instead of one.

## 1. The passage limit

- **Decision**: 512 tokens of text per passage, counted with bge-m3's own tokenizer. Tables are
  not counted (§3).
- **Rationale**:
  - RAGFlow's general parser defaults to `chunk_token_num` 512 (`rag/app/naive.py:1135`,
    v0.27.3 `8090ffd8ba60`).
  - RAGFlow counts with tiktoken's cl100k (`common/token_utils.py:55-61`, `:144-148`). Here the
    tokenizer is the embedding model's own, because the limit exists so the embedding model
    reads the whole passage. private-gpt also sizes its splits against its embedding model's
    window (`sentence_tree_node_parser.py:153-166`, `2373cc7b9120`), and the project's
    `split_for_model` already counts with bge-m3.
  - On the 71 sample market files the longest text is 377 tokens, so nothing there is cut
    (FR-008).
- **Alternatives, measured on the 71 market files**:
  - MaxKB's default of 500 characters (`ui/src/views/document/upload/SetRules.vue:166-168`,
    `5290738e7fe8`) cuts 34 of their sections.
  - open-webui's 1,024 characters (`backend/open_webui/config.py:1069`, `0666e59d26a4`) cuts 2.
  - Both break FR-008.

## 2. Where a passage is cut

- **Decision**: headings first, as today. A section whose text is over the limit is split after
  each of `\n ! ? ; 。 ； ！ ？`. The pieces are joined in order while the total stays within
  512 tokens, with no overlap. A piece longer than the limit on its own is cut at the limit.
- **Rationale**:
  - RAGFlow's `naive_merge` splits after each delimiter and keeps it with the piece before
    (`rag/nlp/__init__.py:1630-1696`), then merges pieces while the sum stays under the cap
    (`:1434-1480`). Its default delimiter is `\n!?;。；！？` (`rag/nlp/delim.py:88`).
  - RAGFlow keeps a piece larger than the cap whole (`:1437-1440`). MaxKB cuts it at the limit
    when no break is found (`apps/common/utils/split_model.py:347-349`). This plan takes MaxKB's
    rule so that no passage exceeds the limit (SC-001). Without it the central bank file had
    passages of up to 692 tokens: runs of chart numbers with no delimiter in them.
  - Headings first, then size: open-webui's default (`config.py:1061`) and MaxKB's (patterns,
    then `limit`, `split_model.py:379-388`).
- **Alternative**: MaxKB's `smart_split_paragraph`, which looks back from the limit for a full
  stop (`split_model.py:307-354`). It counts characters and does not cut at line ends.
- **Not adopted**: MaxKB's last default pattern splits text at blank lines
  (`pdf_split_handle.py:35`, `split_model.py:482`).
  - For Markdown it would make every paragraph of the 71 market files its own passage
    (FR-008).
  - For PDFs it does nothing: MaxKB's font-size route writes no blank lines (`:131-143`).
  - Measured: in the two Q&As, 2 of 16 and 2 of 8 questions start a passage. The others sit
    inside a passage, after the previous answer (§9).

## 3. Tables

- **Decision**: a table of up to 10 data rows stays whole, as today. A longer one is cut into
  batches of 10 rows, each batch its own passage, with the header row repeated so each batch is
  still a table. Tables are still searched by keyword only, as today.
- **Rationale**: RAGFlow's `tokenize_table` chunks table rows in batches of 10
  (`rag/nlp/__init__.py:574-582`). RAGFlow joins the rows without the header. Here the header is
  repeated because a Markdown table needs its header row to be found as a table.
- **Measured**:
  - The sample `.doc` is one table of 33 rows, 16,617 characters. It becomes 4 passages of at
    most 5,832 characters.
  - Every table in the 71 market files has 9 data rows, so none of them changes.

## 4. Reading PDFs

- **Decision**: read PDFs with pypdf in three steps:
  1. **Read each page and remove its repeated first and last lines.**
     - Up to 10 lines at the top and at the bottom of each page are candidates.
     - Each candidate is compared with the line in the same place on the 2 pages before and
       after it. Digits are replaced first, so "20" and "21" count as the same.
     - A weighted score above 0.5 marks the line as a header or footer, and it is removed.
     - The first page keeps its header and the last page keeps its footer.
  2. **Find the chapters**, as MaxKB does:
     - with an outline, cut at the outline entries;
     - otherwise, if the table of contents links to its pages, cut at those links;
     - otherwise take the most common font size as the body: a line more than 2 points larger
       becomes a level-2 heading, a line more than 0.5 points larger becomes level 3.
  3. **Join lines broken mid-sentence** in the body text: a line break that does not follow 。 is
     removed. Heading lines are not joined.

  The result is Markdown with headings, which then goes through §1 to §3. The code is written
  here, not copied: MaxKB is GPL-3.0.
- **Rationale**:
  - Headers and footers: private-gpt
    `private_gpt/components/ingest/transformations/remove_header_and_footer_transform.py`
    (`2373cc7b9120`):
    - the 10-line candidate window and the first and last pages kept, `:12-16`;
    - digits replaced before comparing, `:36-44`;
    - the score above 0.5, `:57-97` (headers) and `:99-141` (footers);
    - the 2 neighbouring pages, `:143-162` (`win=2`).

    It runs here on each page's text before the pages are joined. MaxKB has no such step.
  - Chapters: MaxKB `apps/common/handle/impl/text/pdf_split_handle.py` (`5290738e7fe8`):
    - the order of the three routes, `:80-95`;
    - outline chapters, `:315-394`;
    - internal links, `:397-470`;
    - font sizes, `:106-143` and `:164-199`.
  - Joining lines: MaxKB applies `re.sub(r"(?<!。)\n+", "", text)` in its outline and link routes
    (`:354-355`, `:444-445`). Here it is also applied in the font-size route, where MaxKB keeps
    each printed line. Without it, the two Q&As had more broken lines than with markitdown
    (ETF 20 → 113).
  - private-gpt also joins Markdown that continues across a page: tables, lists, code blocks
    (`make_continuation_markdown_transform.py:18-39`, `:88-140`). This reader joins all pages
    into one text and makes no tables from PDFs, so a sentence across a page break is handled
    by the line join.
- **Why not markitdown, which reads PDFs today**: markitdown 0.1.9 (`21d9c1d01ecc`) checks each
  page for "form-style" content by word positions (`_pdf_converter.py:120`). It turns every page
  that passes into Markdown tables (`:552-574`), and there is no switch for it. That is where
  sentences became table rows: 2,705 table rows in the central bank file, 53 in the Article 70-1
  Q&A. private-gpt, which the project's ingest follows, no longer tries markitdown first for
  PDFs either. Its own `pdf-inspector` comes first (`private_gpt/components/readers/registry.py:6`).
- **Measured**: each of the three chapter routes occurred:
  - the central bank file has an outline of 53 entries;
  - the AI guidelines have a linked table of contents;
  - the two Q&As have neither and take the font-size route.

## 5. Reading `.doc`

- **Decision**: `office_oxide.to_markdown`.
- **Rationale**:
  - RAGFlow's current parser reads `.doc` with office_oxide (`internal/parser/parser/doc_parser.go:27-28`,
    `:63-64`; `internal/deepdoc/parser/office/engine_cgo.go:23`, `:41`; `91c702e86be3`).
  - office-oxide's Python package installs from a wheel on Windows, macOS and Linux, with no
    other program. Its README lists legacy `.doc` → Markdown (`README.md:202`, `5f4ce46a4e66`).
- **Measured**: the sample `.doc` converts in under a second. The title becomes a heading and the
  comparison table a Markdown table.
- **Alternatives, each needing something beyond Python** (constitution II):

  | Project | How it reads `.doc` | What else it needs |
  |---|---|---|
  | RAGFlow v0.27.3 | Apache Tika (`rag/app/naive.py:1425-1446`) | Java |
  | unstructured | LibreOffice converts to `.docx` (`unstructured/partition/doc.py:60-93`, `1ab3be89b689`) | LibreOffice |
  | open-webui | unstructured (`backend/open_webui/retrieval/loaders/main.py:775-782`) | LibreOffice |
  | Dify | sends it to an Unstructured server when configured (`api/core/rag/extractor/extract_processor.py:175-176`, `b9081dc682ed`); otherwise reads it as plain text (`:226-228`) | a server |
  | markitdown | not supported: `.docx` only (`converters/_docx_converter.py:24-28`) | — |
  | private-gpt | not listed (`registry.py:3-25`); an unknown type is read as text (`parse_component.py:196-198`) | — |
  | MaxKB | lists `.doc` (`doc_split_handle.py:229-230`) but opens it with python-docx (`:238`), which reads only `.docx` | — |

## 6. `.odt`

- **Decision**: refused. The report names the file and says: OpenDocument text is not read; save
  it as `.docx` or PDF.
- **Rationale**:
  - The precedent reads it with pandoc (`unstructured/partition/odt.py:68-125`). That means
    shipping a pandoc binary of 25–41 MB under the GPL (pypandoc-binary 1.17).
  - unstructured itself skips that package on Windows with Python 3.13 (`pyproject.toml:81-84`).
  - `.odt` is not Word, and the scope is Word and PDF.

## 7. `.docx`

- **Decision**: read as today, with markitdown, then cut by §1 to §3.
- **Test file**: no official `.docx` was found. office-oxide can save the sample `.doc` as `.docx`
  (`README.md:206-211`). That file is used for User Story 2, scenario 1. It lives in
  `tests/data/`, not with the official files, and its name and its test say which `.doc` it was
  saved from.

## 8. Sample documents

- **Decision**: `data/documents/` holds only official originals: the four PDFs and the `.doc`.
  `data/documents/SOURCES.md` lists, for each file:
  - its address;
  - its publisher;
  - the date it was retrieved;
  - the basis for republishing it: Article 9 of Taiwan's Copyright Act.

  The two `.odt` files are not shipped. A test checks the refusal with a small `.odt` of its own.
- **Size**: about 8.2 MB, of which the central bank file is 6.6 MB. That file is kept because
  it is the only sample with an outline.

## 9. Conversion defects

Each defect seen in the sample files, with its counts before (today's reader and splitter) and
after (this plan), counted on the four PDFs. The definitions below are for counting only, not
rules in the product:

- a table row is a line starting with `|`;
- a short line has 1 to 3 characters;
- a page-number line is only digits;
- a chart-like passage is at least 40% digits;
- a broken line is a line ending in a Chinese character followed by a line starting with one.

**Fixed**

| Defect | Where, with an example | Before → after | Fixed by |
|---|---|---|---|
| The whole document is one passage | All four PDFs; the central bank file was one passage of 370,787 characters | AI 1 → 65; central bank 1 → 171; 70-1 1 → 7; ETF 1 → 9 | §1, §2, §4 |
| Sentences stored as table rows | Central bank p. 1: `\| 本年 3 月本行調升第 \| 2 戶購屋貸款成數至 \| 6 成後… \|` | Table rows: central bank 2,705 → 0; AI 337 → 0; 70-1 53 → 0 | §4 (not markitdown) |
| Table-of-contents dot leaders | AI guidelines: `第五章 落實透明性與可解釋性 ....... 20` | 9 → 0 lines | §4 (link route) |
| Chart labels as one-to-three-character lines | Central bank: hundreds of lines like `%`, `0`, `40` | Short lines: central bank 554 → 0; AI 101 → 0; 70-1 25 → 1; ETF 23 → 0 | §4 (line join) |
| Lines broken mid-sentence | ETF: `以追蹤證券交易所設計⏎或同意編製之標的指數` | Broken lines: central bank 357 → 0; AI 503 → 0; 70-1 69 → 0; ETF 20 → 0 | §4 (line join) |
| Page numbers inside the text | `20 第五章 落實透明性與可解釋性…` | A page number before a chapter title: central bank 14 → 8; AI 14 → 1; 70-1 1 → 0. Page-number lines: 70-1 7 → 1 | §4 (headers and footers) |
| `.doc` refused | Life insurance model clauses | Refused → 4 passages | §5 |

**Known limits.** Each was looked up; none has a fix without a model.

| Defect | Where, with an example | Before → after | What was checked |
|---|---|---|---|
| Chart numbers inside passages | Central bank: `圖 11 無自用住宅者購屋貸款餘額與占比 … 37,386 75,122 77,388 …` ranks 1 for "第2戶購屋貸款成數"; the answer ranks 4 | Chart-like passages 0 → 17 of 171 (before, the whole file was one passage) | private-gpt checks each page for chart text by rule (`page_quality.py:94-152`: empty table cells, glued numbers, fragmented tokens). When too many pages fail, it does not clean them: it raises and hands the whole file to its next reader (`pdf_inspector/hybrid_pdf_reader.py:258-263`). Its next readers are markitdown, docling and a vision model (`registry.py:6`). RAGFlow finds figures with a layout model. MaxKB, open-webui and Dify do nothing about it. |
| A passage that is only a page number | 70-1: the first passage is `1` | 0 → 1 | It is page 1's first line. private-gpt keeps the first page's header on purpose (`remove_header_and_footer_transform.py:15`, `:92`). |
| Headings that carry a page number | AI guidelines: `前言 1`, `第五章 落實透明性與可解釋性 20`; a footnote link became the heading `17。` | 0 → 9 headings, plus `17。` | MaxKB takes a link's title from the text inside the link on the contents page and removes only dots (`pdf_split_handle.py:602`). When there is none, it takes the target page's first line (`:605-607`). MaxKB's own output carries the same page numbers; it was run as-is for this measurement. |
| Questions not found as headings | ETF and 70-1: the questions are set in the body font | Passages with a heading: ETF 0 of 9; 70-1 shows only the title. Questions starting a passage: ETF 2 of 16, 70-1 2 of 8 | MaxKB's font route finds headings by size only (`:138-143`). Its blank-line pattern does nothing here (§2). Spec FR-003. |
| A clause in a table ranks behind text that shares its words | `.doc` article 1, "本契約的解釋，應探求契約當事人的真意", ranks 3 behind two passages of the AI guidelines | Not searchable → rank 3 | Tables are searched by keyword only. That was decided before this feature and is not changed here. |

Files ingested before this change keep their old passages until they change or the data folder
is removed, because the skip test is the file's SHA-256.
