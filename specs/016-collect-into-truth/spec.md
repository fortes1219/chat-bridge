# Feature Specification: Collect makes truth files as the 71 were made

**Feature Branch**: `016-collect-into-truth` (feature directory; no git branch is tied to it)

**Created**: 2026-11-26

**Status**: Draft

**Input**: User description: "What `collect` brings back must be made the way the files in `data/truth` were made, and be written there: anything else is of no use. The agent goes to the channels; the maintainer ingests with his own command."

## How the truth files were made, and the command step that does each

The 71 files were made in these steps; `collect` does each of them, in this order. A step the
command cannot do is a stop, not something left out.

| Step when the 71 files were made | The command's step |
|---|---|
| Find the events of the period that bear on the collection targets (`docs/truth_format.md` section 1) | The agent, with web search and web reading, lists the events on or after the start date (and on or before `--until`) that bear on the targets, from the channels, leaving out the events already in the folder |
| Find each event's sources: official and company sources first, then media; not the sites whose robots file or terms forbid automated reading; a site that carries a wire's story is named as such (section 5) | For each event the agent names its source pages on the channels, official ones first; the channel list holds no forbidden site; the command reads each page itself under robots.txt |
| One event, one file, with several sources (`sources` is a list; section 1 and line 3) | The command writes one file per event, its sources `s1`, `s2`, … in the order given |
| One item states one fact and cites one source, in that source's language (section 4) | The agent writes each item with the id of its source and the passage of that source it rests on; the command finds the passage in that source's page text |
| Numbers written with Chinese numerals or 萬, 億, 兆, 成, 碼, 民國年 are converted, and each conversion is recorded (section 3) | The agent converts them and lists each conversion; the command refuses a quantity still written with 萬, 億, 兆 or 碼 after a numeral, and adds each conversion to `tests/data/number_conversions.md` |
| Title, `targets`, `markets`, `tickers`, `exposure` from the vocabulary, `significance` with its reason, `keyword_groups` (sections 1 and 2) | The agent writes them; the command checks the exposure words against `docs/exposure_vocabulary.md`, the targets against section 1, the markets against `data/market_series.json` |
| Each item checked against its source by a second reader: does the item say only what the source says | The command finds each passage in its page; then a second run of the agent, separate from the one that wrote the file and given only each item with its passage, answers for each item whether it says only what the passage says; a record with a rejected item is written again once with the reasons, and refused when it fails again |
| The section 當日與之後的行情 computed by a program (section 7) | Feature 013's code writes it into each new file |
| The files put in `data/truth` | The command writes them there (or into `--into`) |
| The maintainer ingests | `collect` ingests nothing; it ends by saying `uv run chat-bridge ingest data/truth` |

## User Scenarios & Testing *(mandatory)*

### User Story 1 - The channels' events become truth files (Priority: P1)

**Acceptance Scenarios**:

1. **Given** the channels and the latest event date among the files in `data/truth`, **When** the person runs `uv run chat-bridge collect`, **Then** the agent is asked for the events on the collection targets on or after that date (on or before `--until` when given), with their source pages on the channels, and told the events already in the folder.
2. **Given** an event and its source pages, **When** its file is made, **Then** it has the front matter and sections of `docs/truth_format.md`, its sources are the pages, each item cites one of them, and its market section is written; it is in `data/truth`.
3. **Given** the same event reported by three channels, **Then** it is one file with three sources.
4. **Given** a story that bears on no collection target (a coffee chain's prices), **Then** it is not an event and no file is written.
5. **Given** an item whose passage is not in the page of the source it cites, an item not in its source's language, an exposure word not in the vocabulary, a target not listed, a market not listed, or a quantity still written with 萬, 億, 兆 or 碼 after a numeral, **Then** the agent is asked once more with the reasons, and when the new record fails too, that event's file is not written and the command names the event and the reasons. Names such as 兆豐金 or 萬一 are not quantities and pass.
6. **Given** an event whose sources were all cited by a file already in the folder, an event the agent, shown the folder's files of the event's date, names as one of them (from the channels or from addresses), or an event dated outside the asked dates, **Then** it is not written.
7. **Given** a run, **Then** it prints as it goes: which agent it asked, the events found, each page read, each file written or refused and why; it ingests nothing and ends with the ingest command.

### User Story 2 - Web addresses become truth files too (Priority: P2)

**Acceptance Scenarios**:

1. **Given** the addresses of article pages or feeds, **When** `uv run chat-bridge collect <address> …` runs, **Then** each page (each feed item's page) is read, and the agent, given all of them, sorts them into events that bear on the collection targets and writes each event as in User Story 1; pages that bear on none are named and not written.

### User Story 3 - What the agent may do (Priority: P1)

**Acceptance Scenarios**:

1. **Given** the search for events, **Then** the agent is started as feature 015 starts it (web search and web reading; Claude Code reads only on the channels' sites).
2. **Given** the writing of an event, **Then** the agent is started with no tool, given its sources' page text as data, and answers in a JSON schema.

## Requirements *(mandatory)*

- **FR-001**: One file per event, named `YYYY-MM-DD-<short English name>.md` as section 1 names files, written into `data/truth` (another folder with `--into`); a name already taken gets a number.
- **FR-002**: The format, the exposure words and the collection targets are read from `docs/truth_format.md` and `docs/exposure_vocabulary.md` and given to the agent; the markets come from `data/market_series.json`. Changing the targets, the exposure words, the section headings, the markets or the rules the agent follows changes what is collected without changing the program; the front matter keys are the program's, and a format that lists another key stops the command.
- **FR-003**: Each item carries its source id and the passage of that source it rests on; the command finds the passage in that page's text (spaces aside) before the file is written; the passage is not written into the file.
- **FR-003a**: Each file is then checked by a second run of the agent, with no tool and no sight of the writing run, given each item and its passage only; it answers, item by item, whether the item says only what the passage says, with a reason for each no.
- **FR-003b**: A record that fails a check of FR-003, FR-003a or FR-004 goes back to the writing run once, with the reasons; the new record goes through every check and the second reader again, and when it fails, the file is not written and the command names the items and the reasons.
- **FR-004**: A quantity written with 萬, 億, 兆 or 碼 right after an Arabic or Chinese numeral, in the title or an item, refuses the file; names and set phrases without a numeral before those characters pass. The conversions the agent lists are added to `tests/data/number_conversions.md` when the files go to `data/truth` (shown in the terminal when they go to another folder), a row already there not added again; each one's original is in its source's page and its result in the title or an item. 成 and 民國年 are converted by the agent and checked by the second reader (FR-003a), which sees the passage.
- **FR-005**: The source rules of section 5 are followed: official and company sources first; only pages on the channels' sites, which hold no site whose robots file or terms forbid automated reading, checked again at the address a page is read at after any redirect; robots.txt followed when a page is read, and that of the site a page redirects to; a site that carries a wire's story named as `site（wire）` in `publisher`; every fact from a page the command opened, so a feed item whose page cannot be read is named and not used (its summary is not a source).
- **FR-006**: The market section of each new file is written by feature 013's code.
- **FR-007**: `collect` ingests nothing; both READMEs give `uv run chat-bridge collect` and `uv run chat-bridge ingest data/truth`, say the files go to `data/truth`, and say how long a run takes and what it costs.
- **FR-008**: The collected-page files of feature 013 (`local_data/collected/`, their own front matter) are not written any more; the auto-ingest of feature 015 is removed.
- **FR-009**: The cost grows with the events and their sources: one agent run for the search (at most the chat's time limit), one request per source page and per robots.txt (spaced per site), two agent runs per event (writing and checking), four when the first record fails; the smallest real run measures the seconds of one event, and the README gives them.

## Success Criteria *(mandatory)*

- **SC-001**: With saved pages and a stand-in agent's records, an event with two sources becomes one file in the format of `docs/truth_format.md`, section by section, every item's passage found in its source.
- **SC-002**: Stand-in records that break each rule of User Story 1 scenario 5 are refused with no file written; 兆豐金 in an item passes.
- **SC-003**: The smallest real run, with the maintainer's consent and through the command he types (`uv run chat-bridge collect <one article address> --into <a copy of data/truth>`): one event becomes one file, checked item by item against `docs/truth_format.md` and its source, and set beside an earlier file section by section; the seconds it took and the terminal output are kept. Whether the search for events was run for real is said in research.md.

## Not done

- Nothing the 71 files have is left out. If a step of the table proves not doable, the work stops and the maintainer is asked.
