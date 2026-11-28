# Research: Prices looked up for the question

Sources were opened on 2026-11-27. A citation `owner/repo@commit:path:line` points at the file as it
was at that commit.

## Packages

| Need | Package | Version | License | Size | Dependency declared in | Called in |
|---|---|---|---|---|---|---|
| The lookups in the split's reply, refused when they are not the shape (decision 1) | pydantic | 2.14.3 | MIT | none added: already a dependency | `fastapi/full-stack-fastapi-template@77e550a:backend/pyproject.toml:10` | `Azure-Samples/rag-postgres-openai-python@ecaafc4:src/backend/fastapi_app/api_models.py:5`, `:93-97` |
| Read a symbol's daily closes over a period from Yahoo (decision 2) | yfinance | 1.8.0 | Apache-2.0 | none added: already a dependency | `TauricResearch/TradingAgents@9fa1196fffbc:pyproject.toml:30` | `TauricResearch/TradingAgents@9fa1196fffbc:tradingagents/dataflows/vendors/yahoo/ohlcv.py:212` |
| Read the Taiwan days Yahoo lacks from FinMind's public API (decision 2) | requests | 2.34.2 | Apache-2.0 | none added: already locked through yfinance | `FinMind/FinMind@d89a84a:pyproject.toml:30` | `FinMind/FinMind@d89a84a:FinMind/utility/request.py:31` |
| The change over a period and the largest fall from a high (decision 3) | pandas | 3.1.1 | BSD-3-Clause | none added: already installed through yfinance | `pmorissette/ffn@cc9299c:pyproject.toml:40` | `pmorissette/ffn@cc9299c:ffn/core.py:1421-1450`, `:1512-1530` |
| Keep one read of a symbol for a day (decision 6) | pandas | 3.1.1 | BSD-3-Clause | none added: already installed through yfinance | `TauricResearch/TradingAgents@9fa1196fffbc:pyproject.toml:21` | `TauricResearch/TradingAgents@9fa1196fffbc:tradingagents/dataflows/vendors/yahoo/ohlcv.py:201`, `:224` |
| Read several symbols at once, while the search runs (decision 7) | anyio | 4.16.0 | MIT | none added: already installed through FastAPI | `fastapi/fastapi@b283119:pyproject.toml:46` | `encode/starlette@63d868e:starlette/concurrency.py:34` |
| Keep each file's `markets` and `event_time` on its document (decision 5) | SQLAlchemy | 2.1.9 | MIT | none added: already a dependency | `Azure-Samples/rag-postgres-openai-python@ecaafc4:src/backend/pyproject.toml:13` | `Azure-Samples/rag-postgres-openai-python@ecaafc4:src/backend/fastapi_app/postgres_models.py:4`, `:54` |
| The lookups and their rows in the page's contract, checked when they arrive (decision 9) | zod | 4.6.7 | MIT | none added: already a dependency | `middleapi/orpc@26175d2:playgrounds/contract-first/package.json:23` | `middleapi/orpc@26175d2:playgrounds/contract-first/src/contract/sse.ts:2`, `:11` |
| The folded prices line under the answer (decision 9) | @nuxt/ui | 4.13.0 | MIT | none added: already a dependency | `nuxt-ui-templates/chat-vue@ce4ef47:package.json:22` | `nuxt-ui-templates/chat-vue@ce4ef47:src/components/chat/Prompt.vue:66-70` |

No package is added.

## Advisories

No package or runtime is added or changed. The lock files are sent to OSV and `npm audit` again
before this feature is delivered, as for every delivery. On 2026-11-28: `uv.lock`, 158 packages,
no advisory; `npm audit`, only the development chain kept before (glob GHSA-3g3m-2fjr-6pw4 and
minimatch GHSA-g3hv-75wg-m249, through `@vue/test-utils` and js-beautify).

## Decisions

### 1. The program names the lookups in the run that splits the question

- **Decision**: The split's reply gains `prices`, a list of `symbol`, `start_date`, `end_date`. The
  service checks each and runs the lookups; the program's tools and network stay off.
- **Rationale**: In the Azure template the planning call returns a search with typed arguments
  (`search_database(search_query, price_filter, brand_filter)`), stops at that first tool call, and
  the service runs it (`Azure-Samples/rag-postgres-openai-python@ecaafc4:src/backend/fastapi_app/rag_advanced.py:59-65`,
  `:76-108`); a second call answers. The split is already that planning call here, so the lookup
  costs no model run. The argument names follow TradingAgents' price tool
  (`get_stock_data(symbol, start_date, end_date)`,
  `TauricResearch/TradingAgents@9fa1196fffbc:tradingagents/agents/tools.py:18-24`).
- **Alternatives**: A tool the program calls while it answers, as TradingAgents' analyst does
  (`tradingagents/agents/analysts/market_analyst.py:5-12`), through MCP for Claude Code and Codex:
  every call is one more model turn over the whole input, and the programs' tools would no longer
  be all off. Not measured here.

### 2. One source, as today

- **Decision**: The closes are read as `collect/closes.py`'s `read_closes` reads them: Yahoo, and
  FinMind for the Taiwan days Yahoo lacks; the trading days are each market's own.
- **Rationale**: It is the reading specs 012 and 013 already checked, on the same series. A symbol
  not in `data/market_series.json` gets its market from spec 011's listings
  (`strategy/store.py`, `market_of`); it has no FinMind backup unless it is a Taiwan listing.

### 3. What the service computes

- **Decision**: For each lookup, the trend: the first and last trading day of the period and their
  closes; the change over the period; the highest and lowest close and their days; the largest fall
  from a high. For each found event in the period, a row with the market section's values for the
  day and after: series, D0, D0's close, the day's change, the next trading day's change, the change
  to D+5, notes. Every day when the period has at most 10 trading days. An event whose rows equal an
  earlier event's names it instead of repeating them.
- **Columns**: The request for the market moves asked for each event's day and what came after.
  The section's other columns (the aligned day, the trading day before, its close and its change)
  were added when the table was laid out; a row without them is 67 characters against 112 (mean of
  1,017 rows measured in T001), so every event fits without leaving any out.
- **Shared rows**: Events of the same day lined up the same way have the same rows; naming the
  earlier event instead, as spec 020 does for repeated tables, keeps every value and saved 2,632 to
  3,001 characters on the holdings question in T001.
- **Rationale**: The total return and the drawdown are defined as in ffn (MIT): last over first
  minus one (`pmorissette/ffn@cc9299c:ffn/core.py:352`), and the lowest of each close over the
  highest close before it, minus one (`:1421-1450`, `:1512-1530`). TradingAgents' analyst treats the
  tool's numbers as the source of truth for exact prices and percentage moves
  (`TauricResearch/TradingAgents@9fa1196fffbc:tradingagents/agents/analysts/market_analyst.py:48`).
  The event rows are the market section's own computation (`collect/moves.py`, `_row`; alignment
  in `collect/markets.py`, `by_moment` and `by_date`), so a US event lines up with the next Taiwan
  session and an event published after a close with the next session, as the format's section 7
  says, and the 71 files' tables check it (SC-002). The trend set is this project's choice, the
  smallest that answers the measured questions; the indicators a strategy is checked against stay
  the user's own (spec 006).
- **Alternatives**: ffn itself: it brings matplotlib, scikit-learn and scipy
  (`pmorissette/ffn@cc9299c:pyproject.toml:36-44`), against the condition that a clone runs with one
  command and little to install. A row on the first session on or after the event's date: a US
  event would line up with a Taiwan session that closed before it.

### 4. What can be looked up, and how much is sent

- **Decision**: Any symbol spec 011 places in Taiwan or the US, and the listed series (A5), but not
  the cash holding (spec 011's listings read `CASH` as a US symbol, and Yahoo has an unrelated share
  under it); at most 40 lookups, periods of at most 366 days, no date after today. The block holds
  at most 30,000 characters, the whole block: every lookup's line first, then each short period's
  days, then the rows by event in the order the events were found, while the block stays within
  the bound, then a line counting what was left out. Forty lookups of short periods could fill
  most of the bound with their lines and days alone, so the days are counted in it too.
- **Bound**: A safety bound, not a tuned value. With every event kept and the short rows, the
  largest block T001 built was 23,632 characters (the holdings question, 6 holdings, 47 events);
  30,000 leaves room for a person with a few more holdings. A question past it keeps every trend and
  the first events found.
- **Rationale**: The request lets the program look up prices for what the question is about, which
  can be a company in the news the person does not hold. The bounds are safety bounds, not tuned:
  a person keeps at most 30 holdings (spec 011) and the sample lists 9 series; a year covers "the
  last half year". Keeping a ranked prefix within a budget is the shape of RAGFlow
  (`infiniflow/ragflow@8090ffd:rag/prompts/generator.py:176-183`) and Onyx
  (`onyx-dot-app/onyx@ec026c5:backend/onyx/tools/tool_implementations/search/search_tool.py:313`,
  `:329-338`).

### 5. The knowledge base keeps each event's timing, not its market table

- **Decision**: `markets` and `event_time` become columns of `documents`, beside `event_date`;
  `ingest` does not store a section headed as the market section, and says how many it left out.
  A knowledge base from before 0.2.0 is not converted: the app clears it and makes it again
  itself, when the service starts or `ingest` runs; the profile and the question records stay.
- **Rationale**: The market numbers now come from the source, so the stored tables have no use,
  and the front matter's keys are kept where `event_date` already is. The count of sections left
  out keeps the rule from being silent for a person's own document that has a section of that
  name.
- **Clearing is the app's work**: an app upgrades its own database when it starts, as open-webui
  runs its migrations on start (`open-webui/open-webui@0666e59d26a4:backend/open_webui/config.py:63-81`),
  and this project already rebuilds an index built with another model, dictionary or layout when
  `ingest` runs (`chat_bridge/ingest/service.py`, `_plan`). The old knowledge base is dropped
  rather than altered because what it holds has to go (its market sections) and what it lacks
  (each file's `markets` and `event_time`) comes only from the files, so making it again from
  the files is the conversion. Only its own tables are dropped (`KNOWLEDGE_BASE_MODELS`): 0.2.0
  changes neither the profile's tables nor the question records', so they are kept. The service
  imports the sample news again as on a first start; the folders a person ingested are not
  recorded, so the terminal says to ingest them again.

### 6. Kept for a day

- **Decision**: One file per symbol under `local_data/price_history/`, holding the closes read and
  when; a lookup the file covers, read less than a day ago, reads nothing. A read that cannot be
  kept is still used, and the next question reads again.
- **A read that cannot be kept**: on Windows a file another question has open cannot be replaced
  (`PermissionError`, WinError 5, measured), and a disk can be full. yfinance does the same with
  its own cache: when the cache cannot be made it goes on without it
  (`yfinance/cache.py`, 1.8.0, `_TzCache.get_db`).
- **Rationale**: TradingAgents keeps one cache file per symbol and reuses it while it is fresh
  (`tradingagents/dataflows/vendors/yahoo/ohlcv.py:146-158`, `:181-193`); its rule serves a file only
  on the day it was written and reads today's bar again after 15 minutes (`:24`). A day is the
  request's; the README says a close published later that day may show only the next day.

### 7. Waiting for the source

- **Decision**: Each request has 10 seconds; the symbols are read at once, in worker threads, while
  the question's sections are searched; a read past its time is "not read". The first Yahoo
  request of a read goes alone, then the rest together.
- **The first request alone**: yfinance makes its cache databases on its first request in a
  process, and `_TzCache.initialise` (`yfinance/cache.py`, 1.8.0) creates its table and sets
  the WAL journal without the lock its manager uses elsewhere. In the first SC-002 run, on a fresh
  container, one of nine series read together failed with "database is locked"; with the first
  request alone, none did.
- **Rationale**: 10 seconds is the limit the service's FinMind and exchange reads already have
  (`chat_bridge/strategy/taiwan_sources.py:32`), taken from yfinance's own default in spec 012.
  Running blocking reads in threads is how Starlette runs them (`encode/starlette@63d868e:starlette/concurrency.py:34`).
  The person waits at most about one request's limit more than today when a source hangs; T001
  and the person-style run measure the usual wait.

### 8. The replay's stand-in for the program's lookups

- **Decision**: With no model in the replay, a case looks up the listed series and holdings whose
  names appear in its question or parts, the holdings for the holdings question, over the span from
  its earliest to its latest found event.
- **Rationale**: It is a fixed rule, so before and after compare the same lookups; the real run
  checks what the programs actually name.

### 9. What the page shows

- **Decision**: The stream's context carries the lookups and the block's contents; under the answer,
  a folded line names how many symbols, the sources and the read time, and opens to the trends and
  rows. Texts, in both languages, for the maintainer to read:
  - 「查了 {count} 檔的行情（{sources}，讀取於 {time}）」 / "Prices of {count} symbols looked up ({sources}, read at {time})"
  - 「{symbol} 的行情讀不到：{reason}」 / "Could not read prices for {symbol}: {reason}"
  - 「這一題沒有查行情：拆題沒有完成。」 / "No prices were looked up for this question: the split did not finish."
- **Rationale**: The page already folds the sources it cites (spec 003); the numbers now come from
  no file, so the page shows where they came from, as the strategy panel names its sources (spec
  012).

### 10. Where the code lives

- **Decision**: `chat_bridge/price_history/`: the closes reader, the markets file and the row
  computation move there from `collect/`, with the lookups, the store and the trend.
- **Rationale**: `collect` stops computing market sections, and `strategy/prices.py` is the live
  prices of the panel. The name follows yfinance's `history` and the daily series it returns
  (`TauricResearch/TradingAgents@9fa1196fffbc:tradingagents/dataflows/vendors/yahoo/ohlcv.py:212`).

### 11. A question about prices alone

- **Decision**: When the question's own search finds nothing, the question is still split if it
  names a holding or a listed series, by symbol or by a name after the synonym list's expansion
  (`data/synonyms.txt`, the expansion search already uses); otherwise it gets the fixed line, as
  today (`chat/service.py`, the early return when no section is found).
- **Rationale**: 0050 and 006208 appear only in the market tables, not in the news text (measured
  2026-11-23), so with the tables out of the knowledge base a question about one day of 006208 can
  find no section, and the fixed line would answer it without prices. The name check is code, so an
  off-topic question still runs no program; a question about a holding or a series runs the split
  and the answer, as any other question. A question that names only another listed symbol and finds
  nothing still gets the fixed line (spec, Not done).

### 12. Two commits

- **Decision**: The chat's lookup and the end of market sections in new files can each be undone on
  its own; at delivery they are proposed as two commits.

## Runs

### T001, before any code (2026-11-28, no model called)

In the test container: the 71 sample files copied without their market sections and ingested
(245 sections); the 26 recorded cases, the four recorded splits of the holdings question and the 9
market questions replayed through today's search; lookups by the stand-in rule of decision 8 (a
market question looks up its own day); the closes read from Yahoo and FinMind; the rows computed
with `collect/moves.py`. Today's input is that of HEAD `3403a5a`, with spec 020.

| Cases | Today (characters) | With this feature | Saved |
|---|---|---|---|
| 26 recorded | 37,168 / 45,624.5 / 62,491 | short rows, every event | 54.3% / 63.9% / 73.0% |
| 4 holdings splits | 69,567 to 79,958 | 38,917 to 43,963; shared rows 36,236 to 41,329 | 42.3% to 46.1%; shared 46.3% to 49.8% |
| 9 market questions | 29,306 / 40,195 / 46,745 | | 62.3% / 71.6% / 77.4% |

- The holdings question's block: 20,738 to 23,632 characters with every event (41 to 47) and the
  short rows; 18,106 to 20,998 with shared rows. With the section's full rows and a bound of
  12,000, only 14 events fit.
- Every market question's own search still finds sections without the market sections (30; 21 for
  the question about 006208), and the asked series' row of the asked day is in the block.
- Reading a symbol took 0.28 to 0.33 seconds, the first 1.42 (with the connection); the 11
  symbols read together 0.37.
- The stand-in names only the series a question spells out: the question about interest-rate and
  AI events and TSMC, 0050 and "the US technology indices" looked up 2330.TW and 0050.TW, not the
  Nasdaq or the semiconductor index. A real split may name more, so that question's block can be
  larger than the 7,261 to 7,700 characters measured.

### SC-002, the answer sheet (2026-11-28, no model called)

In the test container, the 9 listed series read once with `price_history.reading.read_for`
(Yahoo, FinMind for the Taiwan days Yahoo lacked) and each of the 71 files' rows computed with
`price_history.block.event_rows`, against the file's own table, wherever the table has a number:

- 3,015 cells compared (D0, D0 close, the day's change, the next trading day's change, the
  change to D+5), 3,015 the same, 0 different; no row missing.
- 180 cells the files wrote as "沒有資料" now have a number: the days after the latest events had
  not come when the files were written.
- The first run had 2330.TW not read ("database is locked", decision 7); the run above is after
  the fix.

### SC-003, the replay with the feature's code (2026-11-28, no model called)

In the test container: the 71 sample files ingested by the feature's own `ingest` (245 sections;
71 market sections left out and counted); the 26 recorded cases, the four recorded splits of the
holdings question and the 9 market questions through `find_sections` and `gather_sections`; the
stand-in lookups of decision 8 checked by `check`, read by `read_for` with its day's store, the
block by `prices`, the input by `model_input`. Today's input is that of HEAD `3403a5a`, with spec
020.

| Cases | Today (characters) | With this feature | Saved | `<prices>` |
|---|---|---|---|---|
| 26 recorded | 37,168 / 45,624.5 / 62,491 | 10,122 / 15,819 / 26,957 | 52.4% / 63.9% / 73.0% | 0 / 0 / 7,960 |
| 4 holdings splits | 69,567 to 79,958 | 37,292 to 42,410 | 44.9% to 48.3% | 19,175 to 22,079 |
| 9 market questions | 29,306 / 40,195 / 46,745 | 8,211 / 11,110 / 16,341 | 62.3% / 70.3% / 76.3% | 0 / 1,018 / 1,276 |

- The holdings question gave 41 to 47 events' rows, none left out by the bound, 7 or 8 of them
  naming an earlier event's rows.
- For the 8 dated market questions, the asked series' row of the asked day is in the block.
- No `[n]` in any block but a number of `<sources>`; no market section found in any case.
- The stand-in names only what a question spells out, so 16 of the 26 recorded cases looked
  nothing up; a real split may name more.
- The search does not find exactly what today's does: across the 39 cases, 26 of the news
  sections today's search found are not found now and 28 others are; the 26 lie in 7 distinct
  files (11 case and file pairs). In the Codex split of the multi-part question, two of its AI
  capital-spending core files are among them.

### SC-003's cause: tied keyword scores cut where the rows happen to lie (2026-11-28, no model)

In the test container, today's code (HEAD `3403a5a`) and this feature's, each on a knowledge base
it ingested, the 39 cases replayed through the vector index and exactly (`enable_indexscan` off):

- Through the index and exactly, each code finds the same sections: the vector index is not the
  cause.
- Exactly, the two codes still differ by the same 26 sections. Printing each method's candidates
  for three of those searches: the vector candidates are the same entries in the same order; the
  keyword candidates differ from the first entry tied with another. Many keyword scores are equal
  (`ts_rank_cd` normalized gives 0.5, 0.8 and so on), and the candidate query cuts with
  `ORDER BY relevance DESC LIMIT n` and nothing to settle a tie, so which of the tied entries make
  the cut follows how the rows lie in the table, which this feature changes by storing no market
  section. The fault was there before this feature; today's lists are one such draw.
- With the cut made the same way on both codes, the two find exactly the same sections in all 39
  cases, both ways measured: (a) ties broken by section id, as the query's own last
  `ORDER BY score DESC, id` breaks them; (b) every entry tied with the last kept
  (`FETCH FIRST n ROWS WITH TIES`). So this feature itself drops nothing.
- Against today's lists as they were drawn: (a) loses 52 sections and gains 46, the lost in 15
  distinct files (30 case and file pairs); every one of the 20 questions finds as many of its gold
  and facet files as today; of the multi-part question's four cases, the Codex split in Chinese
  finds one institutions' view core file fewer (2026-10-21-bessent-dismisses-ai-systemic-risk)
  and its AI capital-spending core files back to 6, and the two English cases one TSMC core file
  more each. (b) loses 97 and gains 113, in 28 distinct files (57 pairs), and loses more of that
  question's core files. Choosing a tie rule to recover today's files would fit the rule to known
  questions.
- The cut is fixed in a fix of its own, after this feature, with (a): the PostgreSQL manual asks
  for an ORDER BY that "constrains the result rows into a unique order. Otherwise you will get an
  unpredictable subset of the query's rows" (section 7.6, LIMIT and OFFSET).

### SC-004, as a person, with a stand-in program and stand-in prices (2026-11-28)

`uv run chat-bridge` on a fresh local data folder, so the service imported the sample news itself;
a stand-in Claude Code whose split names lookups by the question, a stand-in yfinance with a close
for every weekday ("ZZZZ" has none); the page walked in headless Edge, each prices line read
folded and opened with the mouse:

- "006208 在 9 月 17 日的漲跌": answered; folded line 「查了 1 檔的行情（Yahoo Finance，讀取於 …）」,
  opened to the period and its trading day with the change from the day before.
- A question naming NVDA, ZZZZ and YYYY (the stand-in has no data for ZZZZ and raises a
  connection error for YYYY), walked again after the reasons became codes, on both pages: NVDA's
  trend and its rows for each found event in the period, each event named by file, event date
  and its sources' numbers; 「ZZZZ 的行情讀不到：Yahoo Finance 沒有它的日線收盤。」 and 「YYYY 的行情讀不到：
  Yahoo Finance 沒有正常回應。」 on the Chinese page, "Could not read prices for ZZZZ: Yahoo Finance
  had no daily closes for it." and "… for YYYY: Yahoo Finance could not be read." on the English
  one; the program was given the same in fixed sentences; the sources' own messages are only in
  the record.
- A split that fails: 「這一題沒有查行情：拆題沒有完成。」 under the answer, and the program was given
  the same in `<prices>`.
- The holdings question: 6 symbols looked up; CASH, which the split also named, left out and its
  reason kept in the record.
- The English question on the English page: 4 symbols, the columns and notes in English, no
  Chinese but the files' own names.
- Every split was given the listed series; every answer's input had `<prices>`; Ctrl+C ended the
  service in 7 seconds with no process left and the database stopped. The walk's first try timed
  out on a selector of the walk itself (answer ids are UUIDs), not on the page.

### The start on a 0.1.0 database (2026-11-28, stand-in program and prices)

`uv run chat-bridge` of this version on a copy of a 0.1.0 database in use since 2026-11-18 (the
copy taken while that database's own server was running; PostgreSQL recovered it on start):

| Counted | Before | After |
|---|---|---|
| Documents | 71 | 71 |
| Sections headed 當日與之後的行情 | 71 | 0 |
| `documents.markets` | missing | there |
| Question records | 64 | 65 (one question asked) |
| Holdings, targets, proposals | 7, 7, 3 | 7, 7, 3 |

The terminal said the knowledge base was made by an earlier version (`documents.markets is
missing; documents.event_time is missing`), so it was cleared and is made again, and to ingest
any folder of one's own again; the service then ingested the sample news (71 files, 245
sections). A question about 006208 was answered with its sources and its prices. Ctrl+C ended the
service with no process left.

## To measure

- SC-005: whether each program names the lookups in the split as asked, and the block's size with
  what it names.
