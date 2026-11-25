# Feature Specification: Asking about your own documents

**Feature Branch**: `008-own-documents` (feature directory; no git branch is tied to it)

**Created**: 2026-11-25

**Status**: Draft

**Input**: User description: "A person who clones the repository can put their own Word, PDF, text and Markdown files in, ingest them with one command, and ask the chat about them. The sample news must then not be mixed into the answers, and the chat page and the answering program must not still talk about market news. The strategy screen stays an investment demo."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Replace the sample with my documents (Priority: P1)

The repository ships sample market news, which the service ingests when the knowledge base is
empty. A person who wants to try their own documents puts them in a folder and runs one command
that makes the knowledge base hold that folder's documents and nothing else.

**Why this priority**: answering from the person's own documents is what the demo is for; the
sample is only a starting point.

**Independent Test**: start from the sample knowledge base, run the command on a folder of other
documents, ask a question, and check that every source comes from that folder.

**Acceptance Scenarios**:

1. **Given** a knowledge base holding the sample news, **When** the person runs `chat-bridge ingest <folder> --replace`, **Then** the folder's readable documents are stored, every other stored document is removed with its sections, and the command lists the documents it removed.
2. **Given** that, **When** the person asks a question in the chat, **Then** every source of the answer is a document from the folder.
3. **Given** a file deleted from the folder, **When** the command runs again with `--replace`, **Then** that file's document is removed.
4. **Given** the same command without `--replace`, **When** it runs, **Then** it adds and updates the folder's documents and removes none of the others, as before, and when the knowledge base holds documents that are not in the folder, it says how many and that `--replace` keeps only the folder's.
5. **Given** a folder in which no file can be read, **When** the command runs with `--replace`, **Then** nothing is removed, the command says why, and it exits with a failure code.
6. **Given** a knowledge base that was replaced, **When** the service starts again, **Then** the sample news is not ingested again.

---

### User Story 2 - The chat speaks about my documents (Priority: P1)

Once the knowledge base holds the person's documents, the chat page and the answering program
treat them as documents, not as market news.

**Why this priority**: sample questions about the central bank, or instructions about market
events, would mislead both the person and the model on someone else's documents.

**Independent Test**: replace the knowledge base, open the page, and read the empty chat and the
question box; ask a question and read the instructions the program received.

**Acceptance Scenarios**:

1. **Given** a knowledge base holding the sample news, **When** the page opens, **Then** the sample questions about that news are shown, as before.
2. **Given** a knowledge base without the sample news, **When** the page opens, **Then** no sample question is shown, and the question box invites questions about the ingested documents.
3. **Given** either, **When** the question box is empty, **Then** its hint does not name market news, in both languages.
4. **Given** any question, **When** the answering program is started, **Then** its instructions describe the sources as sections of the documents in a knowledge base, not as market news, and still say how to read a market table when one is among the sources.
5. **Given** any answer, **When** its notice is shown, **Then** it says the answer was written by AI from the documents in the knowledge base, not from public data.

---

### Edge Cases

- Two folders ingested one after the other without `--replace` both stay, as before. A file stored under the same path from each folder is the same document to the knowledge base, as before.
- A question record or a proposal keeps the sources it was given; removing their documents does not change it.
- Word and PDF files carry no event date, so an answer from them says that the data has no date, as before.
- The synonym table is the file the person edits (`data/synonyms.txt`), as before; with other documents they can change or empty it.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: `chat-bridge ingest <folder> --replace` MUST leave the knowledge base holding the folder's readable documents and no other: every stored document that is not one of them is removed with its sections and search entries, in the same transaction as the folder's documents are written.
- **FR-002**: The command MUST list each document it removed for not being in the folder, apart from the documents removed because their file can no longer be read.
- **FR-003**: Without `--replace`, the command MUST behave as before: it adds and updates and removes only the stored versions of the folder's files that can no longer be read. When the knowledge base then holds documents that are not in the folder, the command MUST say how many, and that running it with `--replace` keeps only the folder's documents, so documents mixing in is never silent.
- **FR-004**: With `--replace`, when no file in the folder can be read, the command MUST remove nothing, say that it removed nothing and why, and exit with the failure code.
- **FR-005**: The service MUST keep ingesting the sample news only when the knowledge base is empty, so a replaced knowledge base stays as the person made it.
- **FR-006**: The instructions given to the answering program, for answers, for splitting a question and for revision answers, MUST NOT describe the knowledge base as market news. The paragraph on market tables stays, as it applies only to sections with that heading.
- **FR-007**: The sample questions MUST be data that comes with the sample news, in both languages, and the service MUST send them to the page only while the knowledge base holds the sample news; otherwise it sends none. The page MUST show the questions it is sent and none when it is sent none. This replaces spec 003 FR-014, which had the page always show its own sample questions.
- **FR-008**: The question box's hint MUST invite questions about the documents in the knowledge base, in both languages.
- **FR-009**: The README MUST say how to use one's own documents: where to put them, the command with `--replace`, what it removes, and that the sample comes back only if the knowledge base is emptied.
- **FR-010**: The notice sent with every answer MUST say the answer was written by AI from the documents in the knowledge base, not from public data, in both languages.

### Key Entities

- **Sample questions**: a few questions about the sample news, each in Traditional Chinese and English.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: In the tests, after `--replace` with a folder of other documents, a search on a question about the sample news returns no section of the sample news.
- **SC-002**: In the tests, a `--replace` on a folder with nothing readable leaves every stored document in place.
- **SC-003**: In the tests, the service sends the sample questions while the sample news is stored and none after it is replaced, and the page shows none then.
- **SC-004**: No instruction file given to the answering program names market news as the knowledge base.

## What it changes elsewhere

| Where | Before | After |
|---|---|---|
| 003 FR-014 | The page always shows its own four sample questions. | The page shows the sample questions the service sends; the service sends them only while the sample news is stored (FR-007). |
| 001 answer instructions | "You answer questions about market events from the sources you are given." | The sources are sections of the documents in a knowledge base (FR-006). |
| 001, 003 notice | "This answer is generated by AI from public data and is not investment advice." | The answer is generated by AI from the documents in the knowledge base (FR-010). |
| 005 `ingest` | Adds and updates; removes only the stored versions of unreadable files. | The same, plus `--replace` (FR-001 to FR-004). |

## Assumptions

- The person's documents are in one folder, subfolders included; to keep two folders, they put both under one.
- The strategy screen and its revision answers stay about investment; only their opening sentence stops naming market events as the knowledge base.
