# Feature Specification: Real long Word and PDF documents

**Feature Branch**: `005-long-documents` (feature directory; no git branch is tied to it)

**Created**: 2026-11-21

**Status**: Draft

**Input**: User description: "The demo must take the kind of long document people really have: legal texts, insurance clauses, regulators' guidance, mostly Word and PDF. Turn them into Markdown, cut them into passages that are useful, and find them. No OCR. So far only hand-written Markdown and one tiny Word file have been tried."

## What was measured before writing this

Seven real documents published by Taiwan's financial regulators and central bank were downloaded
and run through the present `ingest` reader and splitter (no model, no database):

| Document | Type | Result today |
|---|---|---|
| Guidelines for the use of AI in the financial industry | PDF, 933 KB | read; **one passage of 49,260 characters** |
| Central bank post-meeting press conference material | PDF, 6.6 MB | read in 11 s; **one passage of 370,787 characters** |
| Q&A on Article 70-1 of the Securities Investment Trust and Consulting Act | PDF, 215 KB | read; one passage of 5,676 characters |
| Q&A on exchange-traded funds | PDF, 300 KB | read; one passage of 6,113 characters |
| Model clauses for life insurance policies (2006) | `.doc`, 160 KB | **refused: unsupported file type** |
| Amendment comparison tables for two model clauses (2018) | `.odt`, 28 KB each | **refused: unsupported file type** |

- The splitter cuts at Markdown headings. Text taken from a PDF has none, so every PDF becomes a
  single passage however long it is.
- In the converted text: ordinary sentences are turned into table rows when they hold numbers;
  page numbers and repeated page headers sit inside the text; lines break in the middle of
  sentences; chart axis labels appear as hundreds of one-to-three-character lines.
- No official document in `.docx` was found. The Word documents regulators publish are `.doc` and
  `.odt`.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - A long PDF is cut into passages that can be found (Priority: P1)

A person ingests a real long PDF and asks about something inside it. The search returns the
passage that holds the answer, not the whole document and not nothing.

**Why this priority**: a document that becomes one passage of tens of thousands of characters
cannot be searched by meaning and cannot be handed to the model. For real PDFs the demo does not
work at all today.

**Independent Test**: ingest the four sample PDFs into a fresh knowledge base, count and measure
the passages, and search for the sentences below.

**Acceptance Scenarios**:

1. **Given** the four sample PDFs are ingested, **When** their passages are counted, **Then** each document has more than one passage and no passage is longer than the limit set in the plan.
2. **Given** the ETF Q&A is ingested, **When** the search is run for its own first question, "何謂指數股票型基金？投資人如何買賣指數股票型基金？", **Then** the passage holding that question and its answer is among the first 8 results.
3. **Given** the Article 70-1 Q&A is ingested, **When** the search is run for its own first question, "本法第70條之1規範之對象包括哪些?", **Then** the passage holding its answer is among the first 8 results.
4. **Given** the AI guidelines are ingested, **When** the search is run for "落實透明性與可解釋性", **Then** a passage from that chapter is among the first 8 results, and it does not come from the table of contents.
5. **Given** the central bank material is ingested, **When** the search is run for "第2戶購屋貸款成數", **Then** a passage that states the loan-to-value figure is among the first 8 results.
6. **Given** a passage found in scenarios 2 to 5, **When** it is read, **Then** it shows the chapter or section heading it sits under wherever the PDF itself marks headings (an outline, linked contents, or larger type), and no sentence in it is split across table cells.

---

### User Story 2 - Real Word documents are read, or refused with a reason that helps (Priority: P1)

A person puts the Word documents they really have into the folder. Each one is either ingested
or named in the report with the reason and what to do about it. None is skipped in silence.

**Why this priority**: legal and insurance texts mostly arrive as Word. The official ones found
are `.doc` and `.odt`, which today's reader refuses with only "unsupported file type".

**Independent Test**: ingest a folder holding a `.docx`, a `.doc` and an `.odt` and read the
report.

**Acceptance Scenarios**:

1. **Given** a long `.docx`, **When** it is ingested, **Then** it is cut into passages under the same limits as a PDF, and a sentence taken from it is found by the search. No official `.docx` was found, so this is checked on a `.docx` saved from the sample `.doc`; it is a test file and is labelled as converted, not shipped as an official document.
2. **Given** the sample `.doc` (model clauses for life insurance policies), **When** it is ingested, **Then** it is cut into passages under the same limit, and a clause taken from it is found by the search.
3. **Given** a sample `.odt`, **When** it is ingested, **Then** it is listed in the report as a type that is not read, with the reason and what the person can do.
4. **Given** a folder mixing readable and unreadable files, **When** it is ingested, **Then** the readable ones are ingested and the exit code and report say how many were not, as today.

---

### User Story 3 - What converts badly is known and written down (Priority: P2)

For each sample document, a reader can see what was lost or damaged in conversion, with the place
in the original, and which of those defects the feature fixed.

**Why this priority**: retrieval quality on real documents is decided here, and a defect nobody
listed is a defect nobody will fix or disclose.

**Independent Test**: read the defect list against the original files.

**Acceptance Scenarios**:

1. **Given** the sample documents, **When** the defect list is read, **Then** each kind of defect names the documents it was seen in, gives an example of what came out, and gives its count before and after.
2. **Given** a defect the feature fixes, **When** the same document is ingested again, **Then** the passage no longer shows it; a defect that is not fixed is stated as a known limit.
3. **Given** a sentence broken into table cells in the present output (for example the first lines of the Article 70-1 Q&A), **When** the document is ingested after this feature, **Then** that sentence is searchable as a sentence.

---

### User Story 4 - The sample documents ship with the demo (Priority: P2)

The repository carries a small set of real long documents next to the sample market events, each
with its source address and the reason it may be republished.

**Why this priority**: someone evaluating the demo should see it work on real documents without
hunting for files.

**Independent Test**: read the folder and its source list; ingest it on a fresh clone.

**Acceptance Scenarios**:

1. **Given** a fresh clone, **When** the sample document folder is read, **Then** every file has its source address, publisher, date retrieved and the legal basis for republishing it.
2. **Given** a fresh clone, **When** `chat-bridge ingest` is run on that folder, **Then** it completes and reports each file.
3. **Given** the sample market events, **When** they are ingested after this feature, **Then** their passages, search results and yield numbers are the same as before.

---

### Edge Cases

- A scanned PDF with no text layer: refused as today, with the reason. No OCR.
- A PDF whose pages are mostly charts: the chart labels do not become passages of their own.
- A document with real tables: the table stays a table and stays with the text around it.
- A very long document (hundreds of pages): ingest finishes, and its cost grows with the document's length, not with the size of the knowledge base.
- A document changed and ingested again: its old passages are replaced, as today.
- A document with headings (hand-written Markdown, a Word file with heading styles): still cut at its headings; the size limit applies only inside a section that is too long.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: A document MUST be cut into passages whose text does not exceed a stated limit, whether or not the text has headings. Where the text has headings they are still used first. A table does not count toward the text limit; a table longer than a stated number of rows is cut into batches of that many rows.
- **FR-002**: A cut MUST fall at a natural break (the end of a paragraph, a question, a sentence), never in the middle of a sentence when a break exists within reach.
- **FR-003**: Each passage MUST carry the heading it sits under wherever the document marks headings: Markdown headings, a PDF outline, a linked table of contents, or larger type. A question or title set in the same type as the body text is not recognised as a heading; it stays in the passage text, and that is a known limit.
- **FR-004**: Text that is not content (table-of-contents dot leaders, lines of one to three characters from chart axes, page numbers, repeated page headers) is removed where a cited rule removes it. What remains after the feature is listed in `research.md` as a known limit, with examples.
- **FR-005**: Ordinary sentences MUST NOT be stored as table rows. Real tables stay tables.
- **FR-006**: `.docx`, `.pdf` and `.doc` MUST be read. `.doc` is Word's older format and is what official Word documents are actually published in. It is read through a library that installs with the project's own dependencies; nothing beyond Python, Node.js and the logged-in assistant program may be required on the reader's machine ("clone and run"). If measurement on the sample `.doc` shows the library cannot read it usefully, `.doc` is refused with a reason and a way forward, and that is reported as a known limit.
- **FR-013**: `.odt` is not a Word format and is not read. It MUST be refused with a reason that says so and what the person can do (save it as `.docx` or PDF). Reading it elsewhere means shipping a separate converter program of 25 MB or more under another licence, which this demo does not take on.
- **FR-007**: No file may be skipped without being named in the report with its reason.
- **FR-008**: The sample market events MUST ingest and search exactly as before: same passages, same yield numbers.
- **FR-009**: The repository MUST carry the sample long documents in their own folder, apart from the market events, with a source list giving for each file its address, publisher, date retrieved and the basis for republishing.
- **FR-010**: A list of conversion defects MUST be delivered in `research.md`: for each kind of defect, the documents it was seen in, an example, the count before and after, and whether it was fixed or is a known limit.
- **FR-011**: Every rule this feature adds (the size limit, where to cut, what to remove, how each file type is read) MUST come from a precedent cited in `research.md`, with the numbers measured on the sample documents before and after.
- **FR-012**: No OCR is added.

### Key Entities

- **Sample document**: a real document shipped with the demo; its file, source address, publisher, date retrieved, basis for republishing.
- **Passage**: as today, plus the limit on its length and the heading or question it sits under when the text itself had no Markdown headings.
- **Conversion defect**: a document, a place in it, what the original shows, what came out, fixed or known limit.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Each of the four sample PDFs yields more than one passage, no passage has more text than the stated limit, and no table passage has more rows than the stated number (today: 370,787, 49,260, 6,113 and 5,676 characters in one passage each).
- **SC-002**: All four searches of User Story 1 return the expected passage among the first 8 results.
- **SC-003**: Every sample Word file is either searchable or reported with a reason and a way forward; 0 files are skipped in silence.
- **SC-004**: After the feature, the sample market events give the same passage count and the same yield numbers (55 of 60, 0 of 60, 25 of 26, 26 of 26, 2 of 3).
- **SC-005**: The defect list covers every sample document, and each defect is marked fixed or known limit.
- **SC-006**: Asked in the chat, the first question of the ETF Q&A is answered from that document with its source shown (one real run, with the maintainer's consent).

## Assumptions

- The sample documents are official texts of Taiwan's Financial Supervisory Commission, its Securities and Futures Bureau, and the central bank. Under Article 9 of Taiwan's Copyright Act, laws, orders and official documents, including texts drafted by civil servants in the course of duty, are not subject to copyright. The basis is recorded per file.
- The largest sample (6.6 MB) may be left out of the repository if the plan finds it too heavy to ship; the measurements on it are kept either way.
- No official `.docx` was found. The plan either finds one whose republication is allowed or states plainly that the `.docx` scenario was verified on a document that is not shipped.
- Most projects read `.doc` through LibreOffice, a Java service or a hosted service, none of which fits "clone and run". One large project reads it with a small native library that also ships as a Python package for Windows, macOS and Linux; that is the route taken here, after measuring it on the sample `.doc`.
- Out of scope: OCR, citing page numbers in answers, uploading documents through the chat page, and changing how passages are ranked.
