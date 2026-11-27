# Feature Specification: Repeated tables and notes sent once

**Feature Branch**: `020-repeats-sent-once` (feature directory; no git branch is tied to it)

**Created**: 2026-11-27

**Status**: Draft

**Input**: User description: "Optimize what is sent to the answering program before it answers."

## Why

Replayed on 26 recorded questions, the input the answering program gets is 43,997 to 67,261
characters (median 51,462.5); on the question that asks to adjust the holdings over the last two
months, 82,432 to 93,502 before the strategy block. Market tables are a median of 67% of it on the
26 and 72.5% to 73.3% on the holdings question. Events on the same day carry the same table rows,
and every table starts with one of two identical note lines.

Making the search keep fewer sections does not work: every smaller quota measured, except one that
saves under 4%, loses a file or a table row that today's search finds (research, decision 1). So
this feature changes no search and drops no data: it sends a repeated table or note once.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Each table and note is sent once (Priority: P1)

The answering program gets every section the search found, in the same order with the same
numbers; a table or note line that is the same as one already sent in that input is replaced by a
line naming the section that sent it.

**Acceptance Scenarios**:

1. **Given** two sections, [3] and [9], whose table lines are the same, character for character, **When** the input is built, **Then** [3] has its table and [9] has `(same table as [3])` in its place; the rest of [9], its header and its own notes included, is as before.
2. **Given** a quoted note line in [9] that is the same as one in [3], **When** the input is built, **Then** [9] has `(same note as [3])` in its place.
3. **Given** two tables that differ in any character, **When** the input is built, **Then** both are sent whole.
4. **Given** a section with no table or note sent before, **When** the input is built, **Then** it is sent as before.
5. **Given** any question, **When** its sources reach the page and its record is written, **Then** both hold every section's whole text, as before; only the program's input changes.
6. **Given** the 26 recorded questions, the 9 questions about market numbers and the four recorded splits of the holdings question, replayed through the search, **When** each input is built, **Then** every distinct table row of today's input is still in it, and the input is shorter (decision 3).

### User Story 2 - Answers still quote the right market numbers (Priority: P1)

1. **Given** a question whose answer quotes a table that was sent as a pointer, **When** the program answers, **Then** the numbers it quotes are those of the table the pointer names, with their trading dates, and it cites the section of the event it is talking about.

## Requirements *(mandatory)*

- **FR-001**: In the input given to the answering program, a table block (consecutive lines that start with `|`) that is the same, character for character, as a block an earlier section sent is replaced by one line `(same table as [n])`, when that line is shorter than the block; otherwise the block is sent as it is.
- **FR-002**: A quoted line (a line that starts with `>`) that is the same as one an earlier section sent is replaced by one line `(same note as [n])`, when that line is shorter; otherwise it is sent as it is. A lone `>` in a quotation is never replaced.
- **FR-003**: `n` is the number of the first earlier section that sent that block or line; a block or line repeated inside one section is sent as it is there, so a section never points at itself. The sections, their order, their numbers and their headers are unchanged, and every other line is sent as it is.
- **FR-004**: The answer's input and the revision's input, which are both built by `model_input`, follow FR-001 to FR-003.
- **FR-005**: The answer prompt and the revision prompt say what the two lines mean: the table or note is that of section `n`, and it also belongs to the section the line is in; to cite the section of the event being talked about.
- **FR-006**: The sources sent to the page and the sections kept in the record are unchanged. The input the record keeps is the one sent, so it is the folded one and shorter.
- **FR-007**: The README in both languages says that a repeated table or note is sent once.

## Not done

- No table, row, series or section is left out; whether fewer tables could be sent is not decided
  here.
- The search, its quotas and the parts are unchanged.
- A table written without a leading `|` is not compared, and is sent whole.
- How much faster an answer is, is not claimed: the time may go mostly into writing the output.
  The real run measures it.

## Success Criteria *(mandatory)*

- **SC-001**: Fast tests: the same table twice is sent once with the pointer; tables that differ are both sent; a repeated note line gets its pointer; a section's own notes stay; a block or line no longer than its pointer, a lone `>` and a repeat inside one section are sent as they are; the page's sources and the record's sections are unchanged; every distinct table row is in the input.
- **SC-002**: Replay in the test container, no model called: the 26 recorded questions, the 9 market questions and the four holdings splits, today's input against this feature's; every distinct table row present in both; the characters saved reported with the pointers counted; how many replacements fall outside market sections.
- **SC-003**: Real run, with consent, at Default. The holdings question with each program: asked through the service with this feature, then the same sections, unfolded, given to the same program as today's input (no new split), so before and after are compared on one split and one set of sections. The English question about 0050 with Claude Code and a question about 006208 on 2026-09-17 with Codex, through the service, so each program reads the pointers on two questions. For each: the sections, the characters sent, the split's seconds, the first words, the end, the input and output tokens; the market numbers quoted are checked against the tables.
