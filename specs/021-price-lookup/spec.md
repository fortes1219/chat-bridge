# Feature Specification: Prices looked up for the question, not tables sent with every file

**Feature Branch**: `021-price-lookup` (feature directory; no git branch is tied to it)

**Created**: 2026-11-27

**Status**: Draft

**Input**: User description: "Stop writing market tables into new news files. Leave the existing
files as they are. For the dates a question is about, let the answering program look prices up
from the market data source; keep every other access as it is. The program computes the changes.
Keep what was looked up for one day."

## Why

The market tables attached to every found file are 67% of the answering program's input on 26
recorded questions (median; 62% to 76%) and 72.5% to 73.3% on the question that asks to adjust the
holdings over the last two months. That question carries 44 to 50 tables whose trading days add up
to 72 to 77 days of the same 9 series. Without the tables the 26 inputs are 8,283 to 18,399
characters (median 15,255); the holdings question's are 18,096 to 20,505 plus its strategy block.

## Assumptions (readings of the request, for the maintainer to confirm)

- **A1** The answering program does not reach the market data source itself. It names what to look
  up, the symbols and the dates, in the run that already splits the question; the service reads
  the source, lines up the trading days, computes the changes and hands the program the numbers.
  The program's tools and network stay off, as today. (The request has the changes computed by
  code; a model that fetched the data itself would compute them.) What follows: the run that
  writes the answer cannot look anything more up after reading the news; the rows of the found
  events' dates are added by the service itself.
- **A2** The 71 existing files are not changed on disk. Their market sections are no longer stored
  in the knowledge base: `ingest` leaves them out, and the numbers come from the lookup.
- **A3** `chat-bridge truth` no longer writes a market section into a new file, and
  `chat-bridge collect <news files>` no longer computes one; the format's section 7 describes the
  existing files only.
- **A4** When the source cannot be read, the answer says the prices could not be read; nothing is
  put in their place.
- **A5** Any symbol the service can place in a market can be looked up: a Taiwan or US listing as
  spec 011 recognizes it, or a series of `data/market_series.json`. The user's holdings and the
  listed series are given to the program by name, so it can name them; other companies in the news
  are named by the program.
- **A6** A knowledge base made before 0.2.0 is not converted, and clearing it is the app's work, not
  the person's: when the service starts or `ingest` runs on one, the knowledge base's tables are
  dropped and made again, and the service imports the sample news again on its own. The profile
  (holdings, targets, rules) and the question records are not the knowledge base's and are kept;
  folders of a person's own documents are not known to the app, so the terminal says to ingest
  them again.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Prices for what the question is about (Priority: P1)

**Acceptance Scenarios**:

1. **Given** "依照過往2個月的事件，調整我現在的持股策略", **When** the question is split, **Then** the split also names each holding and the period, and the program answering is given, for each holding, the period's trend and a row for each found event in the period, computed by the service, and no market table from the files.
2. **Given** "006208 在 9 月 17 日的漲跌", **When** it is answered, **Then** the program is given 006208's close on 2026-09-17 and its change from the trading day before, computed by the service, and quotes them with the date.
3. **Given** the English question about interest-rate and AI capital-spending events and how TSMC, 0050 and the US technology indices moved, **When** it is answered, **Then** each found event has, for each series looked up, a row with the values a market section gives that series for that event on the day and after: D0, its close, the day's change, the next trading day's change and the change to D+5.
4. **Given** an event published after the Taiwan close on its date, or a US event, **When** its row is computed, **Then** it is lined up as the format's section 7 lines it up, by its `event_time` when the file has one and otherwise by its date and first market, so no row puts a move from before the event after it.
5. **Given** a question about no market, **When** it is split, **Then** nothing is looked up, the input has no prices block, and the page shows no prices line.
6. **Given** a lookup whose symbol the service cannot place, a date in the future, a period longer than allowed, or more lookups than allowed, **When** it is checked, **Then** that lookup is left out, the record says why, and the rest goes on.
7. **Given** the source cannot be read for a symbol, or does not answer within its time limit, **When** the answer is written, **Then** the input and the page say the prices of that symbol could not be read, and the answer says so; no other number takes their place.
8. **Given** the split fails or runs out of time, **When** the answer is written, **Then** nothing is looked up, and both the input and the page say that no prices were looked up for this question; the answer does not say the data has no prices.
9. **Given** the same symbol and period looked up again within a day, **When** it is answered, **Then** the source is not read again.
10. **Given** more rows than the block may hold, **When** the block is made, **Then** every lookup's trend is kept; the days of short periods, then the rows by event in the order the events were found, are kept while the whole block stays within its bound; and a line says how many trading days' and events' rows were left out.
11. **Given** a question whose own search finds no section but which names a holding or a listed series, by symbol or by a name (after the synonym list's expansion), such as "006208 在 9 月 17 日的漲跌", **When** it is asked, **Then** it is split and its prices looked up as any question, and the program answers from `<prices>`; it is not answered with the fixed line that the data has nothing on it.
12. **Given** a question whose own search finds no section and which names no holding and no listed series, **When** it is asked, **Then** it is answered with the fixed line, as today, and no program is run.
13. **Given** two found events whose rows are the same (the same day, lined up the same way), **When** the block is made, **Then** the later one names the earlier one's file instead of repeating the rows.
14. **Given** the user's holdings include cash, **When** the question is split, **Then** cash is not listed to the program and is never looked up.
15. **Given** any `<prices>` block, **When** it is read, **Then** every `[n]` in it is the number of a section in `<sources>`; events are named by file and event date, never by a number of their own.

### User Story 2 - The person sees where the numbers came from (Priority: P1)

1. **Given** an answer for which prices were looked up, **When** it has ended, **Then** under it, beside the sources, a folded line says how many symbols were looked up, from which sources and when they were read; opened, it shows each symbol's trend and rows as the program was given them, and any symbol not read with the reason.
2. **Given** the line, **Then** the sources are named as the strategy panel names them (Yahoo Finance and its terms; FinMind and the exchanges' open data for the Taiwan days Yahoo lacks).

### User Story 3 - New news files carry no market table (Priority: P2)

1. **Given** `uv run chat-bridge truth`, **When** it writes a file, **Then** the file has no market section and the run reads no daily closes.
2. **Given** one of the 71 existing files, **When** any command of this feature runs, **Then** the file is not changed.

### User Story 4 - The knowledge base keeps each event's timing, not its market table (Priority: P2)

1. **Given** `uv run chat-bridge ingest <folder>`, **When** a file is written, **Then** its front matter's `markets` and `event_time` are kept with it, and its market section is not stored.
2. **Given** a found event with `markets` and no `event_time`, **When** its rows are computed, **Then** they are lined up by its date and first market, as the format's section 7 lines up the 71 existing files.
3. **Given** a found file with no event date or no `markets` (a person's own documents), **When** the rows are made, **Then** it has no rows; the trends of the lookups are given as for any question.
4. **Given** a knowledge base made before 0.2.0, **When** the service starts or `ingest` runs, **Then** the knowledge base is cleared and made again without the person doing anything, the terminal says so, the sample news is imported again by the service, and the profile and the question records are kept.
5. **Given** a knowledge base whose index was built another way (another dictionary, keywords, model or entry layout), **When** the service starts, **Then** the index is rebuilt in place, as `ingest` rebuilds it, so no question meets the old one.

## Requirements *(mandatory)*

- **FR-001**: The split's reply also has `prices`: a list of lookups, each `symbol`, `start_date` and `end_date` (YYYY-MM-DD). The split prompt lists the user's holdings, cash left out, and the series of `data/market_series.json` by symbol and names.
- **FR-002**: A lookup is kept only when the service can place its symbol (A5) and it is not the cash holding's symbol, its dates are real days, `start_date` is not after `end_date`, `end_date` is not after today, and the period is at most 366 days; at most 40 lookups are kept, the first ones listed. What is left out is recorded with the reason.
- **FR-003**: For each kept lookup the service reads the daily closes from the sources it already reads (Yahoo; FinMind for the Taiwan days Yahoo lacks) and computes: the first and last trading day of the period and their closes; the change over the period; the highest and lowest close with their days; the largest fall from a high. For each found file whose event falls in the period, it computes a row with the market section's alignment and values (docs/truth_format.md section 7) for the day and after: the series, D0, D0's close, the day's change, the next trading day's change, the change to D+5 against the trading day before D0, and the notes. An event is named in `<prices>` by its file and event date, with the numbers of its sections in `<sources>`; an event whose rows equal an earlier event's names that event's file instead of repeating them. No `[n]` appears in `<prices>` but a number of `<sources>`. When the period has at most 10 trading days, every trading day has a row.
- **FR-004**: The program is given these numbers in a `<prices>` block, as data, after the sources and before the question; the numbers come from the service only, never from the source's own text. The block holds at most 30,000 characters, a safety bound, kept as US 1 scenario 10 says (research, decision 4).
- **FR-005**: A symbol whose closes cannot be read, or not within 10 seconds a request, is listed in `<prices>` and on the page as not read, with the source named and why (no daily data, or the source could not be read), in a fixed sentence: the service sends the page a reason code to word in its language, and the source's own message goes to the record only. A read that cannot be kept for the day is still used.
- **FR-006**: What was read is kept for one day: a lookup covered by a stored read less than a day old reads nothing.
- **FR-007**: The reads run while the question's sections are searched, several symbols at once.
- **FR-008**: `ingest` does not store sections headed as the format's market section, and its report says how many it left out, so a person whose own document has a section of that name sees it was not stored. The chat no longer leaves them out of its searches or attaches them to found files, as there are none.
- **FR-009**: The answer and revision prompts say what `<prices>` is, that its numbers are the service's, to quote them with their days, and not to say the events caused them; that news is cited by its source's `[n]`, and that a market number from `<prices>` carries no `[n]`, as the page names where the prices came from.
- **FR-010**: The stream's context carries the lookups and what the program was given, for the page (US 2).
- **FR-011**: `ingest` keeps each file's `markets` and `event_time` on its document, beside its `event_date`.
- **FR-012**: `chat-bridge truth` writes no market section and reads no closes; `chat-bridge collect` no longer takes news files; the 71 existing files are not changed.
- **FR-013**: The record of a question keeps the lookups asked for, those kept, those left out and why, and whether each read came from the source or the stored day.
- **FR-014**: The READMEs and `docs/truth_format.md` say where market numbers come from now, that a close published later the same day may show only after the stored day ends, and that a knowledge base from before 0.2.0 is cleared and made again by the app itself when the service starts or `ingest` runs (A6), the profile and the question records kept, and a person's own folders ingested again.
- **FR-016**: When the service starts, a knowledge base an earlier version made is cleared and made again (its tables only), and an index built another way is rebuilt in place, as `ingest` already does for an index; `ingest` clears an old knowledge base the same way before it writes. The page's message for a knowledge base made by another version says to start the service again, not to delete anything.
- **FR-015**: When the question's own search finds no section, the question is still split if it names a holding or a listed series by symbol or name after the synonym expansion; otherwise it gets the fixed line with no program run, as today. The answer prompt lets the program answer from `<prices>` when `<sources>` is empty.

## What this changes

| Earlier | What it said | Now |
|---|---|---|
| 007 (search each part), FR-014 | Each found file's market section comes with it | None is stored (FR-008); prices from the lookup |
| 007, the question's own 8 kept first | The 8 include market sections that rank | No market section is stored to rank |
| A knowledge base of 0.1.0 | Its market sections and its tables | Cleared and made again by the app, not converted (A6, FR-016) |
| The service's start, a database of another version | Stopped with what to delete | Clears an old knowledge base and rebuilds an old index itself (FR-016) |
| 013 (collect), news-file mode | `collect` computes a file's market section | Retired (FR-012) |
| 014 (news to 11-25) | The new news files carry market sections from `collect` | The files to come carry none |
| 016 (collect into truth) | `truth` adds the market section | Retired (FR-012) |
| `docs/truth_format.md` section 7 | How the section is computed | The existing files only; the same rules line up the lookup's rows |
| README, `collect` on news files | The command and what it writes | Removed |
| Answer and revision prompts | Sections headed 當日與之後的行情 hold market tables | `<prices>` holds the service's numbers |
| Constitution IV | Programs read market numbers the service hands them as data | Unchanged: the lookup is the service's |
| 020 (repeats sent once) | Folds repeated tables | Stays; with no tables it has little to fold |
| Tests of `collect` on news files and of `truth`'s market section | | Deleted with the behavior; the row computation's tests stay with the lookup |

## Not done

- The program does not get tools, network or a market API of its own (A1).
- No intraday prices: daily closes only, as the market section had.
- No indicator beyond FR-003; the indicators of a strategy are the user's own (spec 006), not these.
- The 71 files on disk are not rewritten.
- A knowledge base from before is not converted in place (A6).
- A question whose own search finds no section and that names no holding and no listed series gets
  the fixed line, even when it names another listed symbol the lookup could read (A5, FR-015).

## Success Criteria *(mandatory)*

- **SC-001**: Fast tests: every scenario of User Stories 1 to 4 with a stand-in source and a stand-in program; FR-002's checks, cash among them; the stored day; a failed read and a read past its time; the bound of FR-004; the shared rows; no `[n]` in `<prices>` but a source's number; FR-015 both ways; `ingest` stores no market section, says how many it left out, and keeps `markets` and `event_time`; `truth` writes no market section.
- **SC-002**: The answer sheet: for the 71 existing files and their 9 series, the rows the service computes give the same D0, D0 close, day's change, next trading day's change and change to D+5 as the file's table, cell by cell, wherever the table has a number.
- **SC-003**: Replay in the test container, no model called: the 26 recorded cases, the 9 market questions and the four holdings splits, with lookups by a stand-in rule (research, decision 8); the input's characters before and after, the `<prices>` block's size, and the holdings question's in particular; with the keyword candidates cut the same way on both, today's search and this feature's find the same sections, the market sections aside; against today's lists as drawn, the sections that differ are listed with their cause (research, SC-003's cause); for the market questions and H011, the row of that series on that day is in `<prices>`.
- **SC-004**: As a person, with a stand-in program and stand-in prices: the three questions through the page, the prices line opened, a failed read, a failed split.
- **SC-005**: Real run, with consent, the number of model runs stated before: the holdings question with each program; the English 0050 question; the 006208 question; the numbers quoted checked against the service's; every `[n]` in each answer is a real source, and no event of `<prices>` is cited as one.
