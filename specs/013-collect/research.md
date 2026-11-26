# Research: Collect new knowledge with a command

## Packages

| Need | Package | Version | License | Size | Dependency declared in | Called in |
|---|---|---|---|---|---|---|
| Download an address with limits on size, redirects and private addresses | trafilatura | 2.4.0 | Apache-2.0 | 183,984-byte wheel, with courlan, htmldate, lxml, dateparser and their dependencies | `langroid/langroid@fc879d6:pyproject.toml:67` | `langroid/langroid@fc879d6:langroid/parsing/url_loader.py:312` (`buffered_downloads`, which downloads each address with trafilatura's `fetch_url`, and that with `fetch_response`: `adbar/trafilatura@195a969:trafilatura/downloads.py:499`, `:330`) |
| Keep a page's main text as Markdown with its title, site and date | trafilatura | 2.4.0 | Apache-2.0 | as above | `langroid/langroid@fc879d6:pyproject.toml:67`; `NVIDIA-NeMo/Curator@5a78138:pyproject.toml:222` | `langroid/langroid@fc879d6:langroid/parsing/url_loader.py:317` (`extract(…, output_format=…, with_metadata=True)`); `NVIDIA-NeMo/Curator@5a78138:nemo_curator/stages/text/download/html_extractors/trafilatura.py:103`, its configuration copied and changed at `:90-98` |
| Read an RSS or Atom feed's items | feedparser | 6.0.14 | BSD-2-Clause | 80,668-byte wheel, with feedparser-sgmllib | `lemon24/reader@144f6ec:pyproject.toml:38` | `lemon24/reader@144f6ec:src/reader/_parser/feedparser.py:63` |
| Read the daily closes of the series from Yahoo | yfinance | 1.8.0 | Apache-2.0 | none added: already a dependency | `TauricResearch/TradingAgents@9fa1196fffbc:pyproject.toml:30` | `TauricResearch/TradingAgents@9fa1196fffbc:tradingagents/dataflows/vendors/yahoo/market.py:6`, `:34` |
| Read a Taiwan series' daily closes from FinMind's public API, the second source | requests | 2.34.2 | Apache-2.0 | none added: already locked through yfinance | `FinMind/FinMind@d89a84a:pyproject.toml:30` | `FinMind/FinMind@d89a84a:FinMind/utility/request.py:31` |
| Find the section 「當日與之後的行情」 and the headings around it by their source lines | markdown-it-py | 4.3.0 | MIT | none added: already a dependency | `jupytext/jupytext@6dd0522:pyproject.toml:36` | `jupytext/jupytext@6dd0522:src/jupytext/myst.py:350`, `:384` |
| Change the data sources in the front matter and keep the rest of it as written | ruamel.yaml | 0.19.1 | MIT | 118,102-byte wheel, no required dependencies | `conda/conda@bdbad68:pyproject.toml:45` | `conda/conda@bdbad68:conda/common/serialize/yaml.py:55`, `:60` |

## Advisories

Queried on 2026-11-26 at `https://api.osv.dev/v1/query`:

- ruamel.yaml 0.19.1: none. CVE-2019-20478 (GHSA-xg77-mvwp-crp2), remote code execution through `load`, covers versions through 0.16.7 and has no PyPI package range in OSV; 0.19.1 is outside it, and round-trip mode builds no arbitrary objects.
- yfinance 1.8.0 and requests 2.34.2: as in spec 012's research, none.
- markdown-it-py 4.3.0 and mdit-py-plugins 0.7.0: none.
- trafilatura 2.4.0, courlan 1.5.0, htmldate 1.11.0, lxml 6.1.3, dateparser 1.5.1, charset-normalizer 3.5.3, urllib3 2.8.0, python-dateutil 4.0.0, pytz 2026.6, regex 2026.11.25, tzlocal 5.4.5, tzdata 2026.6, certifi 2026.11.20, feedparser 6.0.14, feedparser-sgmllib 2.1.0: none (the same query for urllib3 1.26.0 returns 24, so an empty answer is a real answer). The versions `uv lock` resolves are queried again after it runs.

Licenses of the dependencies these bring: MIT, BSD-3-Clause, Apache-2.0, PSF-2.0, `Apache-2.0 AND CNRI-Python` (regex) and MPL-2.0 (certifi, already locked through requests). None is GPL, AGPL or LGPL.

## Decisions: collecting pages and feeds

### A. Collect is its own step before ingest, and writes plain records

- **Decision**: `collect` writes one Markdown file with front matter per page; `ingest` reads the folder as it reads any folder. No model writes, summarises or classifies what is collected.
- **Rationale**: The knowledge-base projects read keep the same shape: AnythingLLM's collector writes documents that are then embedded; Jina Reader returns "Markdown with a YAML frontmatter block"; RAGFlow and Quivr turn each feed item into one document. None of them has a model rewrite a page before indexing. A command that knows no subject is what makes the knowledge base whatever is collected.
- **Alternatives considered**: Collecting and ingesting in one step (no project read does it, and the person would not see what was collected before it is answered from).

### B. trafilatura for pages, not markitdown

- **Decision**: trafilatura extracts the main text, as Markdown, with the title, site name and date.
- **Rationale**: markitdown, already a dependency, converts the whole `<body>` of a page, menus and footers included (its HTML converter, read on 2026-11-26), and its feed converter does not keep each item's link. In the article-extraction benchmark of scrapinghub, trafilatura's F1 is 0.958 and whole-page text 0.665.
- **Alternatives considered**: newspaper4k (MIT, F1 0.949; more dependencies, among them pillow and tldextract); readability-lxml (returns HTML, not Markdown); crawl4ai (a browser, an attribution clause for command-line tools, 31 advisories in its history); Firecrawl (AGPL).

### C. feedparser for feeds

- **Decision**: An address whose answer feedparser reads as a feed is a feed; each item's link is collected as a page, and an item whose page cannot be read is written from its own title, summary and link.
- **Rationale**: LangChain's RSS loader reads feeds with feedparser and then each item's linked article; RAGFlow and Quivr write the item's own text. Doing the first and falling back to the second keeps both.

### D. Politeness and safety

- **Decision**: robots.txt is read with `urllib.robotparser` and followed; the command sends its own User-Agent; trafilatura's retry without certificate checking is turned off. Each address is downloaded with `fetch_response` (`downloads.py:337`), one at a time, and a site is asked again only 5 seconds after its last request, robots.txt included: the wait langroid passes to trafilatura's own download loop (`load_download_buffer(dl_dict, sleep_time=5)`, `url_loader.py:311`). The command keeps that wait in its own loop instead of trafilatura's URL store, because the store normalizes the addresses (lowercase host, tracking parameters dropped) and hands back other strings than the ones given, so an answer could not be matched to its address and file (tried on 2026-11-26: `https://Example.com/a?id=1&utm_source=x#frag` came back as `https://example.com/a?id=1#frag`). Two things break with it: a feed item whose page cannot be read is written from the item's own summary, which needs the answer matched back to its item; and a refusal is reported with the reason trafilatura logs, under its own spelling of the address, so the report would name an address the person did not type. Matching them back would mean writing courlan's normalization again by hand (the store uses its internal `normalize_and_split`). The cost of the command's own loop: the same article under two tracking parameters is collected twice, as two files (spec Not done). A test shows two addresses of one site asked at least the wait apart. trafilatura's own limits are kept as they are (`adbar/trafilatura@195a969:trafilatura/settings.cfg:6`, `:7`, `:25`, `:29`; tag v2.4.0): 20,000,000 bytes at most, read as it streams in; 2 redirects; loopback, private and link-local addresses blocked. Its 30-second `DOWNLOAD_TIMEOUT` is the wait to connect and the wait for each read, not a limit on the whole download (`downloads.py:275`), and it sets the retries (`:211-227`): one more read after a read timeout, so a silent site costs 60 seconds; up to 2 retries in all on the statuses it retries, with backoff and `Retry-After` waits of at most 30 seconds each (`MAX_BACKOFF`, `:100`). So an address that does not answer holds the command for about one to two minutes; a site that keeps sending a little at a time is limited only by the 20,000,000 bytes, which the spec's Not done states. The fallback is turned off as its documentation shows, on a copy of `DEFAULT_CONFIG` passed to `fetch_url` (`docs/settings.rst:70-80`; read at `downloads.py:362-368`), as NeMo Curator changes its copy. An answer that is neither HTML nor a feed is refused and named.
- **Rationale**: trafilatura's own crawler checks robots.txt with `urllib.robotparser`; RFC 9309 describes the rules. Collected pages are outside input, so each answer is bounded; the package's own limits are used rather than numbers of our own. Its settings turn on a retry without certificate verification after an SSL error (`settings.cfg` line 33, "set to "off" to refuse unverified connections"), which a command run on a person's machine should not do. A PDF or Word file at an address is a document: `ingest` reads it once it is downloaded.

### E. Where collected pages go

- **Decision**: `local_data/collected/`, another folder with `--into`. Files are named from the site and a short hash of the address, so collecting an address again finds its file; the file is replaced only when its text changed.
- **Rationale**: `local_data/` already holds what belongs to the machine and not to git (the database, the model, the word list). Collected pages are other people's text and stay on the person's machine; some sites' terms forbid republishing the full text. Identity by address and a content hash is how the feed connectors read keep items apart and see changes.

### F. `event_date` is the page's own date

- **Decision**: When the page shows its publication date, it is written as `event_date`, which `ingest` reads for its date filter; when it shows none, there is no `event_date`.
- **Rationale**: Without it, a collected page counts as undated and a question about a period cannot place it; a date the page does not show is not made up.

## Decisions: market moves of a news file

### 1. The moment is the file's own `event_time`, not the time a report was published

- **Decision**: A new front matter key `event_time` holds when the event happened or was made public, with its offset; for a file whose event is a market's close, it is that close. Day 0 of a market is its first session whose close is at or after the moment.
- **Rationale**: A report is often written after the event: the Taiwan close of 2026-11-24 at 13:30 was reported in English at 13:55 and 17:05, so aligning to the report would put day 0 on the next day. A file may also cite background published before the event. The section measures the event, so it needs the event's time.
- **Alternatives considered**: The earliest `published` of the file's sources (wrong for market days and for background sources); intraday prices to split a session at the moment (Yahoo keeps intraday bars only for recent days, so earlier events could not be done the same way).

### 2. Without `event_time`, the date rule of the earlier files

- **Decision**: A file without `event_time` is aligned by date as `docs/truth_format.md` section 7 describes, with the earlier files' first line, which names the date rule, and their note when the event's date has no session.
- **Rationale**: The 71 earlier files have no time; running the command on them gives back their text where the closes are the same (Runs below), so a file is rewritten only when a cell changes; the first line of a file with `event_time` names the moment instead, so the two kinds are told apart.

### 3. `event_time` must agree with `event_date`

- **Decision**: `event_time`'s date in its own offset must be `event_date`; a time without an offset, a value that is not an ISO 8601 time, or another day refuses the file.
- **Rationale**: The two keys describe one moment; a disagreement cannot be settled by the program, so it is refused and named rather than one of them chosen.

### 4. Which days have a session

- **Decision**: A market's sessions are the days its series have a bar for; a bar with no volume whose open, high, low and close are equal is Yahoo's placeholder, not a session; the bar of a session not ended when the data is read is not used. Session hours are the exchanges' regular hours (Taiwan 09:00 to 13:30, New York 09:30 to 16:00).
- **Rationale**: This is how section 7 already finds trading days, so both kinds of file count sessions the same way; no calendar package is added.
- **Limit**: A day Yahoo lacks for every series of a market is not seen as a session, so no backup is asked for it and the days after it count one session early. It has not been seen; it would need Yahoo to miss one day of all five Taiwan series or all four US series at once.
- **Alternatives considered**: An exchange calendar package (exchange_calendars, pandas_market_calendars): it would know early closes and future holidays, which the section does not need for days that have bars.

### 5. A Taiwan day Yahoo lacks comes from FinMind

- **Decision**: For 2330, 2308, 0050, 006208 and the TAIEX (FinMind data id `TAIEX`), a session day Yahoo has no close for is taken from FinMind's daily closes, and the note names the day. FinMind is read only when Yahoo lacks a day the run needs.
- **Rationale**: Yahoo's daily series has missed days (0050 and 006208 on 2026-11-17 and 2026-11-24). FinMind's closes of the TAIEX on 2026-11-16 and 2026-11-17 (41040.08, 40092.11) equal those in `data/truth`, read with one request on 2026-11-26.

### 6. The front matter is edited in round-trip mode

- **Decision**: ruamel.yaml's round-trip mode, with the indentation of the sample files (`indent(mapping=2, sequence=4, offset=2)`, as conda sets it) and no line wrapping, replaces only the `d` entries of `sources`. A test round-trips the front matter of every file in `data/truth` and requires the same bytes.
- **Rationale**: PyYAML, already locked, writes a whole new document: quotes, flow lists such as `[台股]` and key order would change in every file.
- **Alternatives considered**: Editing the front matter as text (a hand-written YAML editor); keeping the data sources in the section instead of `sources` (the format puts them in `sources`, as the 71 files do).

### 7. The markets and series are a data file

- **Decision**: `data/market_series.json` lists each market (time zone, regular session hours) and each series (Yahoo symbol, name in the table, market, second source's id); the command reads it, and a person can change the list without changing the program.
- **Rationale**: Repeated settings are data, read by one loop; the nine series are the sample's choice, not the command's.

### 8. The table is written by joining its cells

- **Decision**: The section's table is written row by row with `|` between the cells.
- **Rationale**: The 71 files' tables have unpadded cells and `|---|` separators; a table package such as tabulate pads and aligns cells, which would make the new tables differ from the earlier ones.

### 9. A change is worked out as the earlier files' were

- **Decision**: A change is `(after / before - 1) * 100`, on the floats Yahoo gives, written with two decimals.
- **Rationale**: `(after - before) / before * 100` gave +0.62% where an earlier file has +0.63% (2415 against 2400, a change of exactly a half); the form above gives back every earlier number (Runs below).

## Runs

### Market moves of the 71 earlier files (2026-11-26, a copy of `data/truth`)

`uv run chat-bridge collect <copy of data/truth>`, reading Yahoo and FinMind:

- 56 files unchanged, byte for byte; 15 rewritten: the 15 files that had cells saying 「沒有資料」.
- In the 15, the cells that changed are 210 cells that said 「沒有資料」 and the data has now (106 day +5, 36 next day, the rest of the rows of events whose day 0 was not in the data then), 24 notes (「Yahoo 回應缺 2026-11-17 這一根」 gone, as Yahoo has that day now; 「2026-11-25 的收盤取自 FinMind」 added for 0050 and 006208), two first lines that now cite `d2` (FinMind gave 0050's and 006208's 2026-11-25), and each file's `d1` `accessed`. No number that was in a file changed, and no other line.

### As a person would (spec SC-006, 2026-11-26)

In a separate local data folder (`CHAT_BRIDGE_LOCAL_DATA`), the maintainer's knowledge base not touched:

- `uv run chat-bridge collect https://en.wikipedia.org/wiki/Federal_Reserve https://www.federalreserve.gov/feeds/press_monetary.xml`: 16 pages written (the article and the feed's 15 items) in 90 seconds, exit 0. Run again: the 15 unchanged pages left alone.
- `uv run chat-bridge ingest <folder>/collected`: 16 files, 91 sections, 81 seconds, exit 0.
- `uv run chat-bridge search "When were the October FOMC minutes released?"`: first, the minutes of the October 27-28 meeting, dated 2026-11-18.
- Seen on the way: the encyclopedia article's `event_date` is 2001-05-16, the day it was first published (htmldate looks for the original date); the README says so. Its text is long enough that one section is over the embedding model's 8,192 tokens, which `ingest` warns about; that is `ingest`'s splitting, not this feature's.
