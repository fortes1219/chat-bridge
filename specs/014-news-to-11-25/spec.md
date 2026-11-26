# Feature Specification: Sample news to 2026-11-25

**Feature Branch**: `014-news-to-11-25` (feature directory; no git branch is tied to it)

**Created**: 2026-11-26

**Status**: Draft

**Input**: User description: "The sample news in `data/truth` ends on 2026-11-17. Add the events from 2026-11-18 to 2026-11-25 in the same format, each with the market moves on the day and after, as the earlier files have them, collected by `uv run chat-bridge collect` (feature 013). The maintainer runs the ingest command himself."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Questions about 2026-11-18 to 2026-11-25 find their events (Priority: P1)

After the maintainer runs `uv run chat-bridge ingest data/truth`, a question about an event of those
days is answered from its file, as a question about an earlier event is.

**Acceptance Scenarios**:

1. **Given** the new files are in `data/truth`, **When** the maintainer runs the ingest command, **Then** it reads them with no error and the files already there are skipped as unchanged.
2. **Given** an event of 2026-11-18 to 2026-11-25 that fits a collection target, **When** a question names it, **Then** the search returns a part of its file.
3. **Given** a new file, **When** it is read, **Then** every item cites a source page that was opened while writing it, in the item's own language, with numbers converted by the rules of `docs/truth_format.md` section 3.
4. **Given** a new file, **When** its section 「當日與之後的行情」 is read, **Then** it was written by `uv run chat-bridge collect` and is aligned to the file's `event_time` when the sources give the time of the event.
5. **Given** an earlier file whose market cells said 「沒有資料」 when it was written, **When** `collect` runs on it, **Then** the cells the data has now are filled and nothing else in the file changes.

## Requirements *(mandatory)*

- **FR-001**: New files cover events with an event date from 2026-11-18 to 2026-11-25 that fit the five collection targets of `docs/truth_format.md` section 1. The events already in `data/truth` are not written again.
- **FR-002**: Each new file follows `docs/truth_format.md` sections 1 to 6: the YAML keys, the exposure words of `docs/exposure_vocabulary.md` only, the three fixed sections, one fact and one source per item, the source rules (official first; sites whose robots file or terms forbid automated reading are not read directly), and the number rules. Each conversion is added to `tests/data/number_conversions.md`.
- **FR-003**: Every fact comes from a page opened while writing the file; nothing is filled from memory.
- **FR-004**: A file has `event_time` when its sources give the time the event happened or was made public (a release time, a filing time, the close for a market-day file); a file whose sources give no such time has none.
- **FR-005**: The section 「當日與之後的行情」 of each new file is written by `uv run chat-bridge collect`, not by hand. The command also runs on the 71 earlier files; it changes only those whose cells now have data, and any other cell it would change is reported before the change is kept.
- **FR-006**: The ingest command is not run by this work; the maintainer runs it.
- **FR-007**: `data/synonyms.txt` is not changed; the names and abbreviations of the new events go into each file's `keyword_groups`.

## Success Criteria *(mandatory)*

- **SC-001**: Every new file is read by the ingest command with no error, in a copy of the knowledge base.
- **SC-002**: Every item of every new file, checked against its source page by a second person who did not write it, says what the page says.
- **SC-003**: The search tests on all sample files are run once at delivery; any question whose result gets worse is reported, and the measured baseline is not changed to hide it.

## Not done

- The text of the 71 earlier files is not changed; only their market cells that now have data.
- Events after 2026-11-25.
- The questions offered on the page (`data/sample_questions.json`).

## Assumptions

- Feature 013 is delivered first.
