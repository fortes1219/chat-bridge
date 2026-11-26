# Feature Specification: Collect from the channels with the person's own agent

**Feature Branch**: `015-collect-channels` (feature directory; no git branch is tied to it)

**Created**: 2026-11-26

**Status**: Draft

**Input**: User description: "A list of channels (the sites to collect from) is kept in the project. The person runs one command: their own logged-in agent (Claude Code or Codex) goes to those channels and finds the new articles, the pages are collected, and they are added to the knowledge base."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - One command from the channels to the knowledge base (Priority: P1)

The person runs `uv run chat-bridge collect`. The command reads the channel list, asks the person's
own logged-in agent to find the articles those channels published since the latest date the
knowledge base has, collects each page the agent names, and ingests what it collected.

**Acceptance Scenarios**:

1. **Given** the channel list and a logged-in Claude Code or Codex, **When** the person runs `uv run chat-bridge collect`, **Then** the agent is asked about the enabled channels only, each page it names is collected into `local_data/collected/`, and the folder is ingested; a question about one of those articles then finds it.
2. **Given** the knowledge base's latest event date, **When** the agent is asked, **Then** it is asked for articles published on or after that date (a page collected again unchanged is left as it was); **given** a knowledge base with no dated document, **then** it is asked for the latest articles, with no date.
3. **Given** the agent names a page that is not on the site of the channel it names it for, or names no listed channel, **Then** it is not collected, and the command names it and says why; the command lists how many pages each channel had.
4. **Given** the agent names a page that cannot be read, **Then** the command names it with the reason, as `collect` does for any address.
5. **Given** neither Claude Code nor Codex is logged in, **Then** nothing is asked or collected, and the command says to log in to one of them.
6. **Given** the agent's answer is not in the asked-for shape, or it runs past its limit, **Then** nothing is collected from it, and the command says so.
7. **Given** a run, **Then** the command says at the start which agent it asked and about how many channels, and prints each page as it is collected, as `collect` does.

### User Story 2 - The agent can only search and read the web (Priority: P1)

**Acceptance Scenarios**:

1. **Given** the agent is Claude Code, **Then** it is started with web search and web reading only, web reading allowed only on the channels' sites and their subdomains, and its answer bound to a JSON schema; no other tool, no command, no file.
2. **Given** the agent is Codex, **Then** it is started with live web search, a read-only sandbox in an empty folder, the tools that run commands or touch files turned off, and its answer bound to a JSON schema.
3. **Given** either program, **Then** its run has the time limit the chat gives a program's answer.

## Requirements *(mandatory)*

- **FR-001**: The channel list is a data file of the project, `data/channels.json`. Each channel has `id`, `name`, `url`, `enabled`, `topics` (free words for what the channel covers) and `note`, the fields of the source list the precedent keeps (research.md). A channel's site is the host of its `url`. The sample list holds the channels the sample news was collected from.
- **FR-002**: What `uv run chat-bridge collect` takes, and what it ingests:
  - no address and no path: it collects from the channels, then ingests the folder it collected into (`local_data/collected`, or `--into`);
  - web addresses: it collects them as feature 013 does, then ingests that folder;
  - paths of news files: it writes their market moves as feature 013 does and ingests nothing; the person ingests those files with `ingest`.
  So collecting from the web ends in the knowledge base with one command.
- **FR-003**: The agent is the person's own logged-in program, chosen as the chat chooses it (Claude Code when it is logged in, else Codex). It returns, in a JSON schema, the pages it found: each page's address and its channel's `id`. The title and date written into a collected file are the page's own, read when the page is collected, never the agent's.
- **FR-004**: The agent's tools are web search and web reading only (User Story 2). It is not given the pages' text to keep: the command collects each page itself, because a web reading tool answers with what another model read from the page, not the page (research.md).
- **FR-005**: A page whose host is not the site (or a subdomain of the site) of the channel it is named for, or that names no listed channel, is refused and named. With no channel enabled, nothing is asked. Pages are collected with `collect`'s rules (robots.txt, waits, limits).
- **FR-006**: Both READMEs say: the agent uses the person's own subscription; what it finds can differ from run to run; a run takes minutes; the collected pages go to `local_data/collected/` and stay on the person's machine. The two steps feature 013 wrote there (`collect`, then `ingest`) become the one command for web pages and channels; news files keep their own `ingest`.

## Success Criteria *(mandatory)*

- **SC-001**: With a stand-in agent that answers fixed pages, one command collects the pages on channel sites, refuses the others, and ingests the folder.
- **SC-002**: The command line each program is started with has exactly the tools and limits of User Story 2.
- **SC-003**: The smallest real run, with the person's consent: the agent finds pages on one channel, one of them is collected and ingested once, and a question finds it; the terminal output is kept for review.

## Not done

- The agent does not write summaries, classify, or fill the news format of `data/truth`.
- The channels' terms are noted in `note`; the command does not read them.
- Web search cannot be limited to the channels' sites; only what is collected is.
- A page on a channel's site that redirects to another site is collected from where it leads (feature 013 follows at most two redirects); only the address the agent named is checked.
- The start date is the knowledge base's latest event date as it is: a document dated in the future by mistake makes the agent look after that date and find nothing.
