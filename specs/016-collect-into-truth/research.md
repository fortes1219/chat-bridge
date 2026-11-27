# Research: Collect makes truth files as the 71 were made

## Packages

| Need | Package | Version | License | Size | Dependency declared in | Called in |
|---|---|---|---|---|---|---|
| Have the person's own Claude Code list the events and their source pages on the channels | Claude Code CLI (installed and logged in by the person) | the person's | proprietary, the person's own install | none added | `hoangsonww/AI-News-Briefing@be45130:briefing.sh:169` (the script starts the CLI it finds) | `hoangsonww/AI-News-Briefing@be45130:briefing.sh:169` (`"$binary" -p …`) |
| Have the person's own Codex do it, with live web search and nothing else | Codex CLI (`@openai/codex`, installed by the person) | 0.166.0 or later | Apache-2.0 | none added | `oEdyb/cron-agents@b006570:config.example.yaml:62-89` | `oEdyb/cron-agents@b006570:config.example.yaml:65`, `:68`, `:79`, `:82`, `:86` |
| Have Claude Code, with no tool, write an event as a record and judge each item, in a JSON schema the program reads | Claude Code CLI | the person's | proprietary, the person's own install | none added | `HKUDS/Vibe-Trading@2134f40:agent/src/providers/claude_cli.py:55-61` (`--restricted`, `--strict-mcp-config`, `--tools ""`, `--no-session-persistence`) | `HKUDS/Vibe-Trading@2134f40:agent/src/providers/claude_cli.py:280-290` (`-p`, `--json-schema`), `:345-346` (no `structured_output` raises) |
| Have Codex, in a read-only sandbox, answer in a JSON schema that a step with write access then reads | Codex CLI | 0.166.0 or later | Apache-2.0 | none added | `openai/codex@af71942:.github/workflows/issue-deduplicator.yml:61-66` (`sandbox: read-only`) | `openai/codex@af71942:.github/workflows/issue-deduplicator.yml:84-98` (`output-schema`), `:371-379` (the writing step parses it) |
| Read each source page's main text, title, site and date | trafilatura | 2.4.0 | Apache-2.0 | none added: feature 013 | `langroid/langroid@fc879d6:pyproject.toml:67` | `langroid/langroid@fc879d6:langroid/parsing/url_loader.py:317` |
| Read an RSS or Atom feed's items | feedparser | 6.0.14 | BSD-2-Clause | none added: feature 013 | `lemon24/reader@144f6ec:pyproject.toml:38` | `lemon24/reader@144f6ec:src/reader/_parser/feedparser.py:63` |
| Check a record's shape and refuse a passage that is not in the text it cites | pydantic | 2.14.3 | MIT | none added: already a dependency | `567-labs/instructor@0acb3a1:pyproject.toml:15` | `567-labs/instructor@0acb3a1:examples/validators/citations.py:9-15`, `:18` (an `AfterValidator` that raises when the citation is not in the text) |
| Read the targets, sections, keys and exposure words from the two docs | markdown-it-py | 4.3.0 | MIT | none added: already a dependency | `jupytext/jupytext@6dd0522:pyproject.toml:36` | `jupytext/jupytext@6dd0522:src/jupytext/myst.py:350`, `:384` |
| Write the front matter in the sample files' layout | ruamel.yaml | 0.19.1 | MIT | none added: feature 013 | `conda/conda@bdbad68:pyproject.toml:45` | `conda/conda@bdbad68:conda/common/serialize/yaml.py:55`, `:60` |
| Read the daily closes for the market section (feature 013's code) | yfinance | 1.8.0 | Apache-2.0 | none added: already a dependency | `TauricResearch/TradingAgents@9fa1196fffbc:pyproject.toml:30` | `TauricResearch/TradingAgents@9fa1196fffbc:tradingagents/dataflows/vendors/yahoo/market.py:6`, `:34` |
| Read a Taiwan day Yahoo lacks from FinMind (feature 013's code) | requests | 2.34.2 | Apache-2.0 | none added: already locked through yfinance | `FinMind/FinMind@d89a84a:pyproject.toml:30` | `FinMind/FinMind@d89a84a:FinMind/utility/request.py:31` |

## Advisories

No package is added. Queried on 2026-11-26 at `https://api.osv.dev/v1/query`: pydantic 2.14.3 and
pydantic-core 2.50.4, none (the same query for pydantic 1.10.0 returns GHSA-mr82-8j83-vxmv, so an
empty answer is a real answer). trafilatura, feedparser, ruamel.yaml, markdown-it-py, yfinance,
requests and their dependencies were queried for feature 013 the same day: none.

## What this changes in features 013 and 015

- Feature 013's collected pages are gone: no file in `local_data/collected/`, no front matter of
  its own, no feed item written from its summary. Its decisions A (no model writes what is
  collected), E (where collected pages go) and F (`event_date` is the page's date) are replaced by
  the decisions below. Its market moves of news files are kept and used for each new file.
- Feature 015's ingest after collecting is gone (its decision 6), and the agent no longer returns
  pages but events with their pages (its decision 1). Its channel list, the agent's start, and the
  check that a page is on its channel's site are kept.
- The command's default folder is `data/truth`.

## Decisions

### 1. Three known pieces put together, not one project's way

- **Decision**: The agent reads and answers in a JSON schema; the program holds the sources, checks
  the record and writes the file.
- **Rationale**: Each piece has a precedent; no project read does the whole. A read-only agent run
  with an output schema, parsed by a later step that has write access: Codex's own issue
  deduplicator (`issue-deduplicator.yml:61-66`, `:84-98`, `:371-379`). A logged-in Claude Code with
  no tool and `--json-schema`, an answer without the structured output raising: Vibe-Trading
  (`claude_cli.py:55-61`, `:280-290`, `:345-346`). A fixed vocabulary as a strict schema's enum,
  checked again by the program, which raises on a value outside it: Codex's issue labeler
  (`.github/scripts/issue_labeler.py:94-105`, `:133-138`). Sources held by the program and cited by
  number, a number past the list removed: STORM (`stanford-oval/storm@fb951af:knowledge_storm/storm_wiki/modules/storm_dataclass.py:271-278`).
- **The other way, not followed**: news projects built on an agent CLI often let the agent write the
  files ("Use the `Write` tool to save the file", `hoangsonww/AI-News-Briefing@be45130:prompt.md:141`;
  the agent saves the report and runs the validator, `draco-agent/tech-news-digest@c3aeafb:references/digest-prompt.md:139-144`). Here the agent reads other people's pages, which can carry instructions, so it gets no tool that writes; what it answers is checked before the program writes anything.

### 2. A passage must be in its page, exactly, white space aside

- **Decision**: Each item carries the passage of its source it rests on. The program looks for the
  passage in the same page text the agent was given, with runs of white space made one space on
  both sides, and refuses the record when it is not there. The passage is not written into the
  file; it is only for the checks.
- **Rationale**: instructor's exact-citation example keeps a fact only when its quote is found in
  the text (`docs/examples/exact_citations.md:37-50`, `:97-100`), and its validator example raises
  (`examples/validators/citations.py:9-15`); spacy-llm finds spans with `str.find`
  (`explosion/spacy-llm@c62a961:spacy_llm/tasks/util/parsing.py:15-45`).
- **Alternatives considered**: Fuzzy matching. instructor's library check allows a few character
  errors (`docs/concepts/citation.md:182`), and langextract accepts fuzzy and partial matches by
  default (`google/langextract@b349919:langextract/resolver.py:184-186`); a partial match of a long
  Chinese passage was reported to cover two characters (langextract issue 289, reported by a
  lookup, not reopened). A passage that is not in the page is what the check is for, so it is not
  loosened.

### 3. A second reader, because a found passage does not make a true item

- **Decision**: After the program's checks, another run of the agent, with no tool and without the
  writing run, gets each item and note with its passage, and answers for each, with a reason,
  whether it says only what the passage says.
- **Rationale**: instructor's own documentation says its citation check "Only validates quotes, not
  the accuracy of extracted facts themselves" (`docs/concepts/citation.md:183`). The shape of the
  check is Ragas' faithfulness metric: a model judges "a series of statements based on a given
  context" and returns a verdict and a reason for each
  (`explodinggradients/ragas@8c63f10:src/ragas/metrics/_faithfulness.py:59-61`, `:73-74`; Apache-2.0).
- **Said plainly**: no news collector read checks its items with a second model run; the
  digest validator read checks form only ("No network or semantic fact checking",
  `draco-agent/tech-news-digest@c3aeafb:scripts/validate-digest.py:4-5`). The second reader is the
  same person's program in a new run, so it is a separate reading, not a different model.

### 4. One more ask with the reasons, then a refusal

- **Decision**: A record that fails a program check or the second reader goes back to the writing
  run once, with the reasons; the new record is checked from the start; a second failure refuses
  the event.
- **Rationale**: instructor gives the validation error back to the model and asks again
  (`instructor/v2/core/retry.py:361-368`), once by default (`max_retries` 1 after the first try,
  `:172`, `:418`), and raises after the last (`:389-397`).

### 5. What bears on the collection targets

- **Decision**: The search is told the targets and the events the folder already has; a record must
  name at least one target from the list; pages given as addresses that bear on none are named and
  not written.
- **Rationale**: A relevance gate is a model's yes or no on the text (LangChain's chain filter,
  `langchain-ai/langchain@30c4e38:libs/langchain/langchain_classic/retrievers/document_compressors/chain_filter_prompt.py:1`, `chain_filter.py:68-79`); here the answer is the list of targets, so a story on none of them cannot become a record.

### 6. Numbers are converted as the 71 were, and checked three ways

- **Decision**: The agent converts the numbers of section 3 of the format and lists each conversion.
  The program refuses a title or item that still has 萬, 億, 兆 or 碼 right after a digit or one of
  〇零一二兩三四五六七八九十百千半, and a conversion whose original is not in its page or whose result
  is not in the file; the second reader sees each item with its passage. Each conversion is added to
  `tests/data/number_conversions.md`.
- **Rationale**: This is how the 71 files were made (format section 3: the conversions are recorded
  in that file). Names and set phrases (兆豐金, 萬一) have no numeral before the character, so they
  pass.
- **Where the record goes**: `tests/data/number_conversions.md` is the record of the sample's
  conversions, so rows are added only when the files go to `data/truth`; with `--into` another
  folder, each conversion is shown in the terminal and nothing in the repository changes, so the
  smallest real run (into a copy) leaves the working tree as it was. A row already in the record is
  not added again. No program reads the record; it is the format's account of the conversions.
- **What the program cannot catch**: a quantity with no numeral before the character, such as
  數萬, 幾億 or 上兆, passes the program's rule; it is left to the agent's instructions and the
  second reader, who sees the passage (an inference from the rule, not measured).
- **Alternatives considered**: Converting in code from the number as written, the practice an AWS
  post on extraction describes ("We ask for the number exactly as written and do unit conversion in
  code", reported by a lookup). It needs a table of Chinese numerals, units and phrases (成, 碼,
  民國年), which this project does not have.

### 7. The rules come from the two docs; the schema is built from them

- **Decision**: The targets (the numbered list after 「採集目標」), the sections (section 二's
  headings, 「（可省）」 marking the optional one), the front matter keys (section 一's table) and
  the exposure words are read with markdown-it-py; the markets come from `data/market_series.json`.
  They become the enums of the record's schema, and the two docs are given to the agent as its
  rules with one file of the folder as an example. A doc that yields none of them, or a key the
  program does not write, stops the command.
- **Rationale**: A format spec read from a file into the prompt is how Fabric keeps its patterns
  (`danielmiessler/Fabric@d3ee2c3:internal/plugins/db/fsdb/patterns.go:147-150`); langextract asks
  for "a high-quality example to guide the model" (`README.md:69`). Enums checked again in code
  follow Codex's labeler (decision 1). The keys are the program's because `ingest` and the market
  section read them.

### 8. Each item in its source's language

- **Decision**: An item citing a source whose `lang` starts with `zh` must have a Han character; an
  item citing a source in another language must have none.
- **Rationale**: Format section 4 ("每一條用它來源的語言寫"). It is a check the program can make, so
  it is not left to the model (the project's rule: what code can decide is not given to a model).

### 9. Source fields

- **Decision**: `url` is the page the command opened; `published` is the date trafilatura reads from
  the page, `unknown` when there is none; `accessed` is the day of the run; `format` is `html`;
  `publisher` and `lang` come from the record. Sources are numbered `s1`, `s2`, … in the order the
  event's pages were given, keeping only those an item cites.
- **Rationale**: Format section 1's `sources` row: 「查不到發表日寫 unknown，不用讀取日頂替」.

### 10. Nothing half made goes into the folder

- **Decision**: The daily closes are read once, for the span of the events' dates (feature 013's
  21 days on each side), before any record is written. Each file is made in a temporary folder,
  feature 013's market section is added to it, and only then is it moved into the folder; its
  conversions are added after.
- **Rationale**: The market section is part of every truth file; a file without it, or a file
  written before its checks, would be a file the 71 are not like. When the closes cannot be read,
  the command stops before spending the agent's runs.
- **A run stopped part way** (Ctrl+C): a file is written beside its name with a `.part` suffix and
  renamed onto the name (`os.replace`), and the part is removed when the write is stopped, so no
  half file is left. A file already in the folder holds its event (decision 11), so the next run
  does not write it again, and its conversions are not added twice. A test stops a run in its
  second event and runs it again. Left open: a run stopped after a file is renamed into the folder
  and before its conversions are added leaves that file's rows out of the record, and the next run
  does not add them, as it does not write the file again.

### 11. An event the folder has is not written again

- **Decision**: The files of the folder dated on or after the start date (by their file names) are
  read; their titles and dates are given to the search, and an event whose source pages are all
  cited by one of them is not written.
- **Rationale**: The start date is the folder's latest event date, and a run picks up where the
  folder ends (feature 015 decision 5), so the events of that day may be in it already. Only those
  files are read, so the cost grows with the run, not with the folder.
- **The same event under other pages**: an event can come back with pages the folder's file does
  not cite, from addresses above all, where the search is not told what the folder has. So the
  writing run, from the channels and from addresses alike, is given the folder's files of the
  event's date (name and title) and answers `same_as`: one of those names, or null; a name means
  the event is not written. The model is given the existing items and returns which ones the new
  one duplicates, as Codex's issue deduplicator does
  (`openai/codex@af71942:.github/workflows/issue-deduplicator.yml:68-98`); `same_as` is a nullable
  enum of those names, written as Codex's issue labeler writes its product
  (`.github/scripts/issue_labeler.py:95-98`). Only the files of that date are read.

### 12. No ingest

- **Decision**: `collect` ends with the ingest command when it wrote a file, and does not ingest.
- **Rationale**: The person ingests with their own command after collecting, as the 71 files were
  ingested.

### 13. A page read at another address after a redirect

- **Decision**: When a page redirects to another site, that site's robots.txt is read and followed
  too; from the channels, the address a page is read at must still be on its channel's site, and
  a page that moved off it is named and not used.
- **Rationale**: The channel list holds only sites whose robots file and terms allow automated
  reading (format section 5); a redirect could lead elsewhere after the check on the address the
  agent gave, and the file's `url` is the address the page was read at.

### 14. The source mark after an item

- **Decision**: An item ending with 。, 」 or ） has its `[sN]` right after it; any other item has
  one space before it.
- **Rationale**: The 71 files do so without exception: 166 items with no space, all ending with
  。; 344 with one space, ending with `.` or `…`. A test writes all 510 lines back as they are.

## Decisions after the first full run

Both lookups were made again from the start (2026-11-26); every line below was opened at the commit
given. These replace decision 3 (the second reader), and the parts of decisions 10 and 11 that
assumed one run searched, read and wrote with the events kept in memory.

### 15. Collecting and making truth files are two steps, with stored material between

- **Decision**: `collect` finds the events and reads their pages, and stores each event in
  `local_data/collected/`; `truth` reads only stored events and makes the files. `truth` reads no
  web page; the daily closes for the market section are the one request it makes.
- **Rationale**: Pipelines that fetch and then hand material to a model keep the two as separate
  stages with files between them:
  - karpathy/hn-time-capsule@ca02ebb: stages run "individually or all at once" (`README.md:33`):
    `fetch`, `prompt`, `analyze`, `parse`, `render` (`:46-50`), one folder per article holding
    `article.txt`, `prompt.md`, `response.md` (`:59-71`); `analyze` reads the stored prompt only
    (`pipeline.py:607-617`). It has no license file: its shape is cited, no code is taken.
  - grbtm/news-briefing-generator@e487450 (MIT): `fetch_content`, then `summarize_articles` with
    `depends_on: [fetch_content]` (`configs/workflow_configs.yaml:28-39`); the summaries are made
    from the stored `feed["scraped_text"]` (`src/news_briefing_generator/tasks/article_summarization.py:155`).
- **What it fixes**: the first version read an event's pages, asked the model, then read the next
  event's pages; the events found were kept in memory, so a stopped run searched again.

### 16. One model run per event, from its stored pages

- **Decision**: `truth` runs the model once per event with that event's stored pages; the agent is
  not given the whole store at once.
- **Rationale**: For many short documents the map shape is the one documented as effective: "Note
  that map-reduce is especially effective when understanding of a sub-document does not rely on
  preceding context. For example, when summarizing a corpus of many, shorter documents."
  (langchain-ai/langchain@9971fd8 `docs/docs/tutorials/summarization.ipynb:125-131`).
  hn-time-capsule makes one request per article (`pipeline.py:625-634`); news-briefing-generator
  one per article (`article_summarization.py:152-157`); "Each article is summarised individually,
  in a separate call, from the scraped text only." (picnet.com.au/blog/building-a-daily-ai-digest-of-global-health-news).
  Claude Code's own example of headless work over many files is one run per file, "Try it on three
  files first" (code.claude.com/docs best-practices.md:554-562).
- **Against one call for all**: the projects that give everything in one call pick headlines or
  write one summary, not one record per item; and a single pass was seen to drop items: "the LLM
  becomes lost towards the end and consistently excludes the last two stories"
  (blog.gdeltproject.org, Claude 2 on a whole broadcast transcript); "They dump all their fetched
  items into a prompt that says "summarize these." … and buries what matters." (dev.to/alanwest).
  No project was found that gives an agent a folder of stored articles and gets many structured
  files back in one run.

### 17. What was collected is removed once its event is done

- **Decision**: Once an event is a file, or the folder already has it, its folder in
  `local_data/collected/` is removed, and the collected folder too when it is left empty. An event
  that fails twice stays stored and is tried again by the next `truth`. Only a folder directly
  under the collected folder, named as `store.py` names event folders and holding an `event.json`,
  is ever removed. With `--into` another folder the events are removed the same way.
- **Rationale**: The maintainer asked for it: what was collected is cleared once the truth files
  are made, so nothing is left in the project. With nothing kept for done events, the store itself
  says what is left to do, as hn-time-capsule's stages skip an article whose output exists
  (`pipeline.py:610`) and write no output for a failed one, so it is tried again (`:639-640`).

### 18. At most five model runs at once, `--workers` to change it

- **Decision**: `truth` keeps at most `--workers` model runs under way at once, 5 by default.
- **Rationale**: 5 is the default of news-briefing-generator (`DEFAULT_MAX_CONCURRENT: int = 5`,
  `article_summarization.py:57`, with `asyncio.Semaphore(max_concurrent)` at `:135`), of NeMo
  Curator's LLM client (`max_concurrent_requests: int = 5`,
  NVIDIA-NeMo/Curator@5a78138 `nemo_curator/models/client/llm_client.py:85`, its semaphore at
  `:152-155`) and of hn-time-capsule's analyze stage (`max_workers: int = 5`, `pipeline.py:591`),
  whose command line names the option `--workers` (`:1453`). Each run uses the person's own
  subscription, so the README says how many run at once.
- **Events of one date**: they are made one after another (one lock per date), because an event
  is shown the folder's files of its date to say whether it is one of them (decision 11), and two
  events of one date made at once could not see each other's file. Events of different dates
  never share those files, so they run at once.
- **Events that end together**: naming the file, writing it, adding it to the list of the folder's
  events, adding its conversions and removing what was collected happen with no wait between them,
  so in the one event loop no other event runs in the middle. A stop cancels every run, and each
  run ends its process tree in its `finally` (`chat_bridge/chat/claude_code.py` `_reply_in_shape`).

### 19. `--limit N`

- **Decision**: `truth --limit N` makes only the first N stored events.
- **Rationale**: hn-time-capsule's `--limit` "Limit number of articles (for testing)"
  (`pipeline.py:1451`; it applies it when fetching, `:502-503`); Claude Code's "Try it on three
  files first" (best-practices.md:562).

### 20. The second model run is removed

- **Decision**: No second model run checks the items; the program's checks and the one more ask
  with the reasons stay.
- **Rationale**: Neither lookup found a news collector that checks its items with a second model
  run; the validator read checks form only ("No network or semantic fact checking",
  draco-agent/tech-news-digest@c3aeafb `scripts/validate-digest.py:4-5`). It made every event two
  model runs, four when sent back. In the one real run, the item it sent back held a fact the page
  had, outside the passage cited. For the 71 files the items were checked against their sources by
  another person after they were written; the reviewer does that before a commit.

### 21. What is stored for an event

- **Decision**: `event.json` holds the event's date and line, the dates it was asked for, when it
  was collected, and for each page its id, the address asked, the address read, title, site and
  date; `s1.txt`, `s2.txt`, … hold each page's text as it is given to the model, the same text the
  passages are looked for in. An event folder is written beside its name and renamed onto it.
- **Rationale**: hn-time-capsule keeps `meta.json` and `article.txt` per article (`README.md:64-66`).
  The input to one run stays far below Claude Code's 10 MB cap on standard input ("Piped stdin is
  capped at 10MB", headless.md:140).

### 22. The search is told what is stored too

- **Decision**: `collect` from the channels tells the agent the events of `data/truth` and the
  events stored in `local_data/collected/` from the start date; an event with the same pages is
  not stored again.
- **Rationale**: Without it a second `collect` before `truth` finds and reads the same events again;
  the folder of an event is named from its pages, so the same pages give the same folder.

## Decisions after the smallest real run of the second version

The reviewer compared the two files of that run (below) with the 71 and found three differences.

### 23. The full stop goes outside the quotation marks, checked

- **Decision**: An item that ends with a full stop inside a closing quotation mark (`."`, `。」`) is
  refused with that reason and asked once more, as with the other checks. The prompt does not
  restate the rule; the format it is given says it (section 4 b).
- **Rationale**: In the run 15 of the 20 English quotations ended `."`. None of the 71 sample files
  ends an item so, and 280 items end with the stop outside (223 `".`, 57 `」。`). A program tells
  this without a model run.

### 24. `event_time` as the format says, with the markets' closes given

- **Decision**: The prompt says what the format's table of keys says: the time a source writes, or,
  in a file about a market's trading day, that market's close. The closes are given between
  `<markets>` tags from `data/market_series.json` (US 16:00 America/New_York, TW 13:30
  Asia/Taipei), so the agent does not write a close from what it knows.
- **Rationale**: The prompt said "only when a source writes the time", the opposite of the format
  for a market's day, and the run's file of the TAIEX's day had no `event_time`. Its market section
  came out the same, aligned by date (format section 7).

### 25. A keyword group that holds two things is not checked by the program

- **Decision**: No program check. The reviewer reads the keyword groups of each file before the
  maintainer commits it.
- **Rationale**: The format says each group is one thing's names. In the run 1 group of 18 held a
  company and its analyst (`[兆豐國際投顧, Mega International Investment Service, 黃國偉, Alex Huang]`).
  Telling a person's name from a company's needs a model run or a list of names, and the project
  has no such list.

## Not verified

- langextract issue 289 and the AWS post were reported by lookups and not reopened here.
- Whether several `claude -p` or `codex exec` runs at once meet the subscription's rate limits: a
  lookup reported a blog post and an issue that hit limits at three to five; not reopened.
- No project read combines a fixed target list, quote checks and an agent CLI; the combination is
  this feature's.

## Runs

### The smallest real run of the second version (2026-11-27, with the maintainer's consent)

In a separate local data folder and into a copy of `data/truth` (71 files), with the maintainer's
logged-in Claude Code:

- `uv run chat-bridge collect https://www.cna.com.tw/news/afe/202611250161.aspx https://focustaiwan.tw/business/202611250017 https://www.federalreserve.gov/newsevents/pressreleases/monetary20261118a.htm`:
  from 12:01:12, 41 seconds, exit 0. The three pages were read, and one sorting run made two
  events: the TAIEX's fall of 2026-11-25 from the two CNA pages (Chinese and English), and the
  Fed's release of the October FOMC minutes on 2026-11-18 from one page. Both were stored.
- `uv run chat-bridge truth --limit 3 --into <the copy>`: from 12:02:01, 208 seconds, exit 0. The
  two events ran at once (different dates). The 2026-11-25 record was refused once (影響股市證據
  item 6 was not in s2's language: an English item with a Chinese name) and written when asked
  again; one conversion, 新台幣1兆1881.99億元 to NT$1.188199 trillion. Files: 2 written, 0 already
  there, 0 not written. Four runs of Claude Code in all: sorting, writing twice, writing again.
- `local_data/collected/` was gone after the run; the repository did not change.
- The reviewer checked each item of both files (30 and 4) against the stored text: each holds,
  and each quoted phrase is the source's. Beside the 71: the same keys in the same order, sources,
  sections, notes of empty sections, market section, closing line and the space before `[sN]`.
  The three differences are decisions 23 to 25.
- The 2026-11-25 file aligns its market section by date; its US next-day column is empty
  (Thanksgiving on 2026-11-26; 2026-11-27 had not closed).
- Not run: the search for events on the channels in the second version; Codex.

### The smallest real run (2026-11-26, with the maintainer's consent)

`uv run chat-bridge collect https://www.federalreserve.gov/newsevents/pressreleases/monetary20261124a.htm --into <a copy of data/truth>`,
with the maintainer's logged-in Claude Code, 16:34:54 to 16:36:32, 98 seconds, exit 0:

- One page read; the sorting run made it one event of 2026-11-24 (the Board's discount rate
  minutes of October 19 and 28).
- The first record failed the second reader on one of 6 statements: an item gave the release date
  and time, which the passage it cited did not hold ("only says 'on Tuesday'"). The record was
  written again with the reason, and all 7 statements of the second one were supported. Five runs
  of Claude Code in all: sorting, writing, checking, writing, checking.
- One file written, `2026-11-24-fed-board-discount-rate-minutes-october-2026.md`: the front matter
  in the sample files' order, `event_time` 2026-11-24T14:00:00-05:00 from "For release at 2:00
  p.m. EST", four items from the release, a note in each of 影響股市證據 and 相關標的, the market
  section (US day 0 on 2026-11-24 with the note that the event fell in that session; Taiwan on
  2026-11-25; 0050 and 006208 of 2026-11-25 from FinMind), and the significance line.
- Beside the earlier `2026-10-28-fomc-holds-rate-two-dissents.md`: the same keys in the same order,
  the same sections and closing line; that file has two sources (the Fed and AP), this one the
  single page it was given. It writes `event_time`, which the earlier files do not have, quoted
  (`"2026-11-24T14:00:00-05:00"`), as a value YAML would read as a time.
- The working tree did not change: no conversion, nothing in the repository written.
- Not run: the search for events on the channels; Codex.

### The maintainer's run of the first version (2026-11-26, about 17:00 to 17:35)

`uv run chat-bridge collect`, from the channels into `data/truth`, as reported by the reviewer from
the terminal the maintainer pasted: the search finished within its limit and found 30 events; after
about half an hour the run was at "Event 3 of 30", and two files of 2026-11-17 had been written
(17:32:27 and 17:33:19). Each event read its pages, then waited for its model runs, before the next
event began; this run is why the two steps were separated (decisions 15 to 22). The search for
events is not run again for the second version: this run showed it working.
