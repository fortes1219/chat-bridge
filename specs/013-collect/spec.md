# Feature Specification: Collect new knowledge with a command

**Feature Branch**: `013-collect` (feature directory; no git branch is tied to it)

**Created**: 2026-11-26

**Status**: Draft

**Input**: User description: "A person who cloned the project collects new material with a command and adds it to the knowledge base with `ingest`. What is collected decides what the knowledge base is for; collecting pages does not depend on what they are about. It collects web pages and feeds into a folder on the person's own machine, and it collects the market moves a news file in the project's format carries. The README gives the commands with uv and says where the collected files go."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Collect web pages, then ingest them (Priority: P1)

The person runs `uv run chat-bridge collect <address> …`, then `uv run chat-bridge ingest
local_data/collected`, and asks about what the pages say.

**Acceptance Scenarios**:

1. **Given** the address of an article, **When** the command runs, **Then** the article's main text is written as Markdown to one file in `local_data/collected/`, with the page's title, address, site name, its own publication date when it shows one, and the time it was collected; menus, footers and scripts are left out.
2. **Given** a collected file, **When** `ingest` runs on the folder, **Then** the file is ingested with no error, and a question about the page finds it.
3. **Given** a page that shows its publication date, **Then** the file's `event_date` is that date, the only place the date is written; **given** a page that shows none, **then** the file has no `event_date`.
4. **Given** the same address collected again, **When** the page has not changed, **Then** the file is left as it was; **when** it has changed, **then** the file is replaced.
5. **Given** an address whose site's robots.txt disallows it, an address that cannot be read, a page with no main text, an answer that takes longer than the time limit or is larger than the size limit, or an answer that is neither a web page nor a feed (a PDF, an image), **Then** nothing is written for it, and the command names it with the reason (for a document such as a PDF: download it and ingest the file); the other addresses are still collected and the exit code says not everything was.
6. **Given** an address on the person's own machine or private network, or an address with a user name or password in it, **Then** it is refused.
7. **Given** a run, **When** it collects, **Then** it says at the start how many addresses there are and that a site is asked only after a wait, and prints each page as it is written, left alone or refused.

### User Story 2 - Collect a feed (Priority: P1)

**Acceptance Scenarios**:

1. **Given** the address of an RSS or Atom feed, **When** the command runs, **Then** each item's linked article is collected as in User Story 1, with the item's own date when the article shows none.
2. **Given** an item whose article cannot be read, **Then** the item's own title, summary and link are written instead, and the file says it holds the feed's summary.

### User Story 3 - Collect the market moves of a news file (Priority: P1)

A news file in the format of `docs/truth_format.md` carries the section 「當日與之後的行情」. The
person runs `uv run chat-bridge collect <news file or folder>`, and the command reads the daily
closes and writes the section and its data sources into the file.

**Acceptance Scenarios**:

1. **Given** a news file without the section, **When** the command runs on it, **Then** the section is added after 「相關標的」 and before 「後續與不同說法」, and the data sources are added to `sources`.
2. **Given** a news file that has the section, **When** the closes have not changed, **Then** the file is left as it was, byte for byte; **when** they have (a day that had no data now has it), **then** the section and its data sources are replaced and nothing else changes.
3. **Given** a file without `event_date` or `markets`, or whose `event_time` is not an ISO 8601 time with an offset, or whose `event_time` falls, in its own offset, on another day than `event_date`, **Then** it is left as it was and named with the reason; the exit code says not every file was done.
4. **Given** the daily data cannot be reached, **Then** no file is changed and the command says which source failed.

### User Story 4 - Day 0 is the first session after the event (Priority: P1)

The moment is the file's `event_time`: when the event happened or was made public, with its time
zone, as the sources give it; for a file whose event is a market's close, that close. Day 0 of each
market is the first trading session of that market that closes at or after the moment.

**Acceptance Scenarios**:

1. **Given** a market-day file whose event is the Taiwan close (`event_time` 2026-11-24 13:30 Asia/Taipei), **Then** the Taiwan series' day 0 is 2026-11-24 and the US series' day 0 is the US session of 2026-11-24.
2. **Given** results published after the US close (16:05 America/New_York), **Then** the US and Taiwan series' day 0 are each market's next session.
3. **Given** a Fed release at 14:00 America/New_York, **Then** the US series' day 0 is that session and its note says the event came during it, and the Taiwan series' day 0 is the next Taiwan session.
4. **Given** a moment on a day a market has no session, **Then** that market's day 0 is its next session.
5. **Given** a file without `event_time`, **Then** it is aligned by date as `docs/truth_format.md` section 7 describes for the earlier files, and the section's first line is theirs, which names the date rule.
6. **Given** any section, **Then** its first line names the moment and the rule.
7. **Given** a file with `event_time`, **When** it is ingested, **Then** it is read as a file without it is.

### User Story 5 - A missing day comes from another source, never an estimate (Priority: P1)

**Acceptance Scenarios**:

1. **Given** a series with a second source of daily closes (the Taiwan series: FinMind), **When** Yahoo lacks a session day the second source has, **Then** the cell uses that close, the note names the day and the source, and the source is listed in `sources`.
2. **Given** a day no source has, or a session not ended when the data is read, **Then** the cell says 「沒有資料」 and the note says why.
3. **Given** a bar with no volume whose open, high, low and close are equal, **Then** it is not a trading day.

### User Story 6 - The README says how (Priority: P1)

**Acceptance Scenarios**:

1. **Given** either README (English and Traditional Chinese), **Then** it gives the `uv run chat-bridge collect` and `ingest` commands together, says the collected pages go to `local_data/collected/`, that they stay on the person's machine and out of git, that deleting `local_data/` deletes them too, that `event_date` is the date the page shows, and that the person is responsible for the sites' terms.

## Requirements *(mandatory)*

- **FR-001**: `chat-bridge collect` takes web addresses, feed addresses, and paths of news files or folders. An address is collected as a page, or as a feed when what it returns is a feed; a path is a news file whose market moves are collected. It runs no model.
- **FR-002**: A page's main text, title, site name and publication date are extracted by an article-extraction package; a feed is read by a feed package. Neither rewrites or classifies the text.
- **FR-003**: Each collected page is one Markdown file in `local_data/collected/` (another folder with `--into`), named from its site and a short hash of its address, so the same address is the same file. Its front matter holds `title`, `url`, `site`, `collected` (UTC time), `event_date` (the page's publication date, only when it shows one; `ingest` filters by it), and `feed` when it came from one.
- **FR-004**: Before reading a site, its robots.txt is read and followed; requests to one site are spaced; the command sends its own User-Agent; a certificate error is an error, never retried without checking; addresses on the person's machine or private network are refused. Each answer has a time limit, a size limit and a limit on redirects; the limits are the article-extraction package's own defaults (research.md).
- **FR-005**: The series and markets of the market moves are data, not code: a file lists each market (its time zone and regular session hours) and each series (its Yahoo symbol, its name in the table, its market, and its second source's id if it has one). The sample file lists the nine series of `docs/truth_format.md` section 7, with FinMind for the TAIEX, 2330, 2308, 0050 and 006208.
- **FR-006**: Day 0 of a market is the first regular session of that market whose close is at or after `event_time`, an ISO 8601 time with its offset whose date in that offset is `event_date`; day −2, −1, +1 and +5 count that market's sessions from day 0. Which days have a session comes from the dates in that market's series. When a file has no `event_time`, the date rule of section 7 is used.
- **FR-007**: The closes are Yahoo's unadjusted daily closes; a day Yahoo lacks comes from the series' second source. A close is used only for a session that has ended. Each series is read once a run, for the span all the files need. The columns, the ex-dividend note and 「沒有資料」 are those of section 7.
- **FR-008**: A news file is written only when its section's cells or notes change, with LF line endings; the rest of the file, its front matter included, is kept byte for byte.
- **FR-009**: `docs/truth_format.md` section 1 adds `event_time`; section 7 describes both rules, which files use which, the series file and the command. Both READMEs carry User Story 6.

## Success Criteria *(mandatory)*

- **SC-001**: Collected from a saved copy of an article page and of a feed, the files hold the main text, the title, the address, the site and the date, and `ingest` reads them with no error.
- **SC-002**: For a fixed set of daily closes, the market cells match the closes and changes worked out by hand, for an event during a US session, after a Taiwan close, on a weekend, and without a time.
- **SC-003**: Run twice with the same data, the command changes nothing the second time.
- **SC-004**: Run on one earlier news file, which has no `event_time`, the command gives the cells the file has, except cells that said 「沒有資料」 and the data has now.
- **SC-005**: The front matter of every file in `data/truth` comes back byte for byte from the round trip the command uses.
- **SC-006**: Run as a person would on this machine before delivery: one public page and one public feed are collected, ingested into a copy of the knowledge base (the maintainer's own is not touched), and found by `uv run chat-bridge search`; the terminal output of each step is kept for review.

## Not done

- No model writes, summarises or classifies collected pages; the news files in `data/truth` are still written in their format by people.
- No crawling: the command reads the addresses it is given and the items of the feeds it is given, not the links in them.
- robots.txt of a site a page redirects to: a download follows at most two redirects, and only the site of the address given is checked.
- Addresses are not normalized: the same article under two addresses (another tracking parameter, another letter case in the host) is collected twice, as two files.
- Pages that need a browser to show their text, logins and paywalls.
- A limit on the whole time of one download: the wait to connect and each wait for data are limited, and the size is, but a site that keeps sending a little at a time is not cut off sooner.
- Intraday prices: the section uses daily closes, so the move of the part of a session after the event is not separated from the part before it; the note says the event came during the session.
- Exchange holidays and early closes are not known in advance: days without a bar are not sessions, and an early close counts as a full session.
