# Feature Specification: Collect makes truth files as the 71 were made

**Feature Branch**: `016-collect-into-truth` (feature directory; no git branch is tied to it)

**Created**: 2026-11-26

**Status**: Draft (revised after the first full run)

**Input**: User description: "What `collect` brings back must be made the way the files in `data/truth` were made, and be written there: anything else is of no use. The agent goes to the channels; the maintainer ingests with his own command." After the first full run: "Collecting is one thing and making truth is another: the articles are collected and stored first, and the stored material is given to the model afterwards to make the truth files. Once they are made, what was collected is cleared, so no rubbish is left in the project."

## What changed after the first full run

The first version did each event from start to end before the next: read its pages, ask the model
to write, ask it again to check, then go on to the next event, with the events found kept only in
memory. A stopped run had to search again, and every event waited for the one before it.

This version has two steps, as pipelines that first fetch and then hand stored material to a model
are built (research decision 15):

1. **Collecting** finds the events and reads their pages, and stores each event with its pages'
   text in `local_data/collected/`. No model writes anything; no truth file is made.
2. **Making truth files** reads only the stored events and makes each into a file in `data/truth`.
   It reads no web page. Once an event is a file, or the folder already has it, what was collected
   for it is removed; when all are made, nothing is left in `local_data/collected/`.

The second reader of the first version (a second model run checking each item) is removed: no news
collector in either lookup checks its items with a second model run, and it doubled the model runs
of every event. The program's checks stay, and so does the one more ask with the reasons. The items
of a file are checked against their sources by the reviewer before the file is committed, as the
71 were.

## The names (shown to the maintainer on 2026-11-26; he did not object)

| What | Name | Where it comes from |
|---|---|---|
| The command that collects and stores | `uv run chat-bridge collect` | kept; the maintainer named it |
| The command that makes truth files from what was collected | `uv run chat-bridge truth` | the maintainer's own words 「產生truth」「整理成Truth」; the precedent's stage names are verbs (`fetch`, `analyze`: karpathy/hn-time-capsule README:46-48) |
| Where collected events are stored | `local_data/collected/` | the folder the maintainer agreed to on 2026-11-26 |
| One folder per event | `local_data/collected/<event_date>-<12 hex>/`, the hex from the event's page addresses | one folder per item, `data/<date>/<item_id>/` (hn-time-capsule README:59-71) |
| In it | `event.json` (the event and each page's address, title, site, date), `s1.txt`, `s2.txt`, … (each page's text) | `meta.json`, `article.txt` (hn-time-capsule README:64-66) |
| Do only the first N stored events | `truth --limit N` | `--limit` "Limit number of articles (for testing)" (hn-time-capsule pipeline.py:1451) |
| How many model runs at once | `truth --workers N`, default 5 | `--workers` (hn-time-capsule pipeline.py:1453); 5 as the default of news-briefing-generator (article_summarization.py:57), NeMo Curator (llm_client.py:85) and hn-time-capsule's function (pipeline.py:591) |
| Up to which date | `collect --until YYYY-MM-DD` | kept |
| Which folder the files go to | `truth --into FOLDER`, default `data/truth` | kept (it was `collect --into`) |

`uv run chat-bridge collect <news file or folder>`, which writes a news file's market section, is
unchanged.

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The channels' events are collected and stored (Priority: P1)

**Acceptance Scenarios**:

1. **Given** the channels and the latest event date among the files in `data/truth`, **When** the person runs `uv run chat-bridge collect`, **Then** the agent is asked once for the events on the collection targets from that date (to `--until` when given), with their source pages on the channels, and told the events `data/truth` already has and the events already stored in `local_data/collected/` from that date, so a second `collect` does not find and read them again.
2. **Given** the events it names, **Then** each event's pages are read under robots.txt, each page that moved off its channel's site is left out and named, and each event with at least one page read is stored as a folder in `local_data/collected/`; nothing in `data/truth` changes and no model writes a record.
3. **Given** an event already stored (the same pages), **Then** its pages are not read again.
4. **Given** a run, **Then** it prints which agent it asked, each event found ("Event i of N"), each page read or left out, each event stored, and ends with the command that makes the truth files.
5. **Given** a search past its limit, **Then** nothing is stored and the message says to ask for fewer days with `--until` or to turn channels off.

### User Story 2 - Web addresses are collected and stored (Priority: P2)

**Acceptance Scenarios**:

1. **Given** the addresses of article pages or feeds, **When** `uv run chat-bridge collect <address> …` runs, **Then** each page (each feed item's page) is read, the agent with no tool sorts them into events on the collection targets, each event is stored as in User Story 1, and pages that bear on no target are named and not stored.

### User Story 3 - Stored events become truth files (Priority: P1)

**Acceptance Scenarios**:

1. **Given** stored events, **When** the person runs `uv run chat-bridge truth`, **Then** each is made into one file in `data/truth` (or `--into`) in the format of `docs/truth_format.md`, from its stored pages only; no web page is read (the daily closes for the market section are).
2. **Given** an event, **Then** the model is run once with no tool and answers with a record; the program's checks of the first version apply (passage in its stored page, source language, exposure words, targets, markets, numbers with 萬, 億, 兆 or 碼, conversions); when they fail, the model is asked once more with the reasons, and when they fail again the event is not written, named with its reasons, kept, and tried again on the next run; each try uses the person's subscription again, and the run's last lines list the events kept.
3. **Given** an event whose pages are all cited by a file in the folder, or that the model, shown the folder's files of its date, names as one of them, **Then** no file is written.
4. **Given** an event made into a file, or that the folder has (scenario 3), **Then** its folder in `local_data/collected/` is removed; when every stored event is done, `local_data/collected/` is gone. Only a folder under `local_data/collected/` that this command stored (its name and its `event.json`) is ever removed. With `--into` another folder the stored events are removed the same way, so making them for `data/truth` afterwards needs another `collect`.
5. **Given** a run stopped part way, **When** it is run again, **Then** the events made are not made again (they are no longer stored), no half file is in the folder, and nothing is collected or searched again.
6. **Given** `--limit 3`, **Then** only the first three stored events are made.
7. **Given** `--workers N`, **Then** at most N model runs are under way at once; the default is 5. Events of one date are made one after another, so each is shown the files the ones before it wrote (scenario 3); events of different dates run at once. Events that end together do not tread on each other: each file gets its own name, and the list of the folder's events and the record of conversions are each changed by one event at a time.
8. **Given** Ctrl+C while model runs are under way, **Then** every one of them stops with every process it started, no half file is left, and the events not finished stay stored for the next run.
9. **Given** a run, **Then** it prints each event's lines tagged with its number, and "Event i of N" with the file written or the reasons it was not as each ends, and ends with `uv run chat-bridge ingest <folder>` when a file was written.

### User Story 4 - What the agent may do (Priority: P1)

**Acceptance Scenarios**:

1. **Given** the search for events, **Then** the agent is started as feature 015 starts it (web search and web reading; Claude Code reads only on the channels' sites).
2. **Given** the sorting of given pages and the writing of an event, **Then** the agent is started with no tool, given the pages' text as data, and answers in a JSON schema; the program writes every file.

## Requirements *(mandatory)*

- **FR-001**: One truth file per event, named `YYYY-MM-DD-<short English name>.md` as section 1 names files, written into `data/truth` (another folder with `truth --into`); a name already taken gets a number.
- **FR-002**: The format, the exposure words and the collection targets are read from `docs/truth_format.md` and `docs/exposure_vocabulary.md` and given to the agent; the markets come from `data/market_series.json`. Changing the targets, the exposure words, the section headings, the markets or the rules the agent follows changes what is collected without changing the program; the front matter keys are the program's, and a format that lists another key stops the command.
- **FR-003**: Each item carries its source id and the passage of that source it rests on; the program finds the passage in the stored text of that page (spaces aside) before the file is written; the passage is not written into the file.
- **FR-003b**: A record that fails a check of FR-003 or FR-004 goes back to the model once, with the reasons; the new record is checked again, and when it fails, the event is not written and stays stored for the next run.
- **FR-004**: A quantity written with 萬, 億, 兆 or 碼 right after an Arabic or Chinese numeral, in the title or an item, refuses the record; names and set phrases without a numeral before those characters pass. The conversions the agent lists are added to `tests/data/number_conversions.md` when the files go to `data/truth` (shown in the terminal when they go to another folder), a row already there not added again; each one's original is in its source's page and its result in the title or an item.
- **FR-005**: The source rules of section 5 are followed when collecting: official and company sources first; only pages on the channels' sites, which hold no site whose robots file or terms forbid automated reading, checked again at the address a page is read at after any redirect; robots.txt followed when a page is read, and that of the site a page redirects to; a site that carries a wire's story named as `site（wire）` in `publisher`; every fact from a page the command opened, so a feed item whose page cannot be read is named and not used. Making truth files reads no web page.
- **FR-006**: The market section of each new file is written by feature 013's code.
- **FR-007**: Neither command ingests; both READMEs give the three commands in order (`collect`, `truth`, `ingest`), say where collected events are stored and that they are removed once made, how many model runs of the person's subscription the commands use and how many at once, and that an event not written is tried again, at that cost, on every later `truth` run.
- **FR-008**: The collected-page files of feature 013 are not written; the auto-ingest of feature 015 is removed; the second model run of the first version (its FR-003a) is removed.
- **FR-009**: Model runs: `collect` from the channels, 1 (the search); `collect` from addresses, 1 (the sorting); `truth`, 1 per stored event, 2 when its first record fails the checks; at most `--workers` at once. Requests: one per page and per site's robots.txt, spaced per site, all in `collect`.
- **FR-010**: A stored event is the event's date, line and asked dates, and for each page its address asked, address read, title, site, date and text; it is written whole (beside its name, then renamed), and an event with the same pages is not stored twice.

## Success Criteria *(mandatory)*

- **SC-001**: With saved pages and a stand-in agent, `collect` stores an event with two pages, and `truth` makes it into one file in the format of `docs/truth_format.md`, section by section, from the stored text, and removes what was stored.
- **SC-002**: Stand-in records that break each check are asked again once and then not written, and the event stays stored; 兆豐金 in an item passes.
- **SC-003**: A `truth` run stopped while two runs are under way ends both, leaves no half file and keeps every unfinished event stored; run again, it makes them and leaves `local_data/collected/` empty.
- **SC-004**: With `--workers 2` and stand-in runs that wait, no more than two are under way at once; events of the same date and name get different names.
- **SC-005**: Only folders this command stored under `local_data/collected/` are removed; another folder is refused and left as it is.
- **SC-006**: The smallest real run, with the maintainer's consent, through the commands he types, in a separate local data folder and into a copy of `data/truth`: `collect <three article addresses>` (one sorting run), then `truth --limit 3` (three to six runs); the three files checked against `docs/truth_format.md` and their stored pages, set beside earlier files; `local_data/collected/` empty afterwards; the seconds of each command and the terminal output kept. The search for events is not run again in the new structure: the maintainer's own run of the first version reached it and found 30 events within its limit (research, Runs).

## Not done

- Nothing the 71 files have is left out. The second model run is removed for the reasons above; the reviewer checks each item against its source before a commit, as was done for the 71.
