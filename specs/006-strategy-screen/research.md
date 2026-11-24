# Research: The strategy screen beside the chat

Sources were opened on 2026-11-23. A citation `owner/repo@commit:path:line` points at the file as it
was at that commit. Pages that carry no commit are cited by URL as read that day.

## Packages

| Need | Package | Version | License | Size | Dependency declared in | Called in |
|---|---|---|---|---|---|---|
| Live prices of the Taiwan and US holdings, the Philadelphia Semiconductor index and the US dollar in Taiwan dollars, with no key | yfinance | 1.8.0 | Apache-2.0 | wheel 158 KB; adds pandas (wheel 8.1 to 13.4 MB), curl-cffi (1.8 to 14.1 MB), cffi, peewee, pytz; numpy, lxml, beautifulsoup4, protobuf, websockets, platformdirs and requests are already locked | `marketcalls/YFinance-Alert-Manager@7f6df14d3e66:requirements.txt:42`; `TauricResearch/TradingAgents@9fa1196fffbc:pyproject.toml:30` | `marketcalls/YFinance-Alert-Manager@7f6df14d3e66:app.py:5`, `:134-139` (live stream); `TauricResearch/TradingAgents@9fa1196fffbc:tradingagents/dataflows/vendors/yahoo/market.py:6`, `:34` (recent closes) |
| Push each new price, with the strategy the service recomputed from it, to the open page | python-socketio | 5.18.1 | MIT | wheel 83 KB; adds python-engineio (61 KB), bidict (36 KB, MPL-2.0), simple-websocket (14 KB), wsproto (24 KB) | `open-webui/open-webui@0666e59d26a4:backend/requirements.txt:7`; `marketcalls/YFinance-Alert-Manager@7f6df14d3e66:requirements.txt:29` | `open-webui/open-webui@0666e59d26a4:backend/open_webui/socket/main.py:137-139`, `:441-444`; `backend/open_webui/main.py:206`, `:812` |
| Receive them in the page | socket.io-client | 4.8.4 | MIT | 1.4 MB unpacked, with engine.io-client 841 KB and socket.io-parser 64 KB | `open-webui/open-webui@0666e59d26a4:package.json:156` | `open-webui/open-webui@0666e59d26a4:src/routes/+layout.svelte:9`, `:175-180` |
| Keep the connection's own state (connecting, connected, disconnected) for the page; it is not server data | pinia | 4.1.0 | MIT | 195 KB unpacked | `vbenjs/vue-vben-admin@e726bc9:packages/stores/package.json:29` | `vbenjs/vue-vben-admin@e726bc9:packages/stores/src/setup.ts:5`, `:42`, `:66` |
| Draw the allocation donut with Nuxt UI's chart component, which needs this package beside it | @tanstack/charts | 1.5.0 | MIT | 3.0 MB unpacked | `nuxt-ui-templates/dashboard-vue@abfe4e74024a:package.json:15` | `nuxt-ui-templates/dashboard-vue@abfe4e74024a:src/components/home/HomeChart.vue:59-62` |
| Ask the person's Claude Code for the answer and a revised strategy in a given JSON shape | Claude Code CLI (`claude -p --output-format json --json-schema`), installed by the person | the person's install | Proprietary (Anthropic); not copyleft | none added: already used for the split | `HKUDS/Vibe-Trading@84af312:agent/src/providers/claude_cli.py:104` | `HKUDS/Vibe-Trading@84af312:agent/src/providers/claude_cli.py:289-290`, `:334` |
| Ask the person's Codex for the same | Codex CLI (`codex exec --output-schema`), installed by the person | 0.166.0 or later | Apache-2.0 | none added: already used for the split | `openai/codex@a0436d6:sdk/typescript/src/exec.ts:50` | `openai/codex@a0436d6:sdk/typescript/src/exec.ts:142-143` |
| Check a proposal and the rules: known fields only, whole percents, every holding once | pydantic | 2.14.3 | MIT | none added: already a dependency | `fastapi/full-stack-fastapi-template@77e550a:backend/pyproject.toml:10` | `Azure-Samples/rag-postgres-openai-python@ecaafc4:src/backend/fastapi_app/api_models.py:5`, `:93-97` |
| Keep the profile, the targets, the rules and the proposals in the local database | SQLAlchemy | 2.0 | MIT | none added: already a dependency | `Azure-Samples/rag-postgres-openai-python@ecaafc4:src/backend/pyproject.toml:13` | `Azure-Samples/rag-postgres-openai-python@ecaafc4:src/backend/fastapi_app/postgres_models.py:4`, `:54` |
| Cards, tables, the side panel and the drawer | @nuxt/ui | 4.13.0 | MIT | none added: already a dependency | `nuxt-ui-templates/dashboard-vue@abfe4e74024a:package.json:14` | `nuxt-ui-templates/dashboard-vue@abfe4e74024a:src/components/home/HomeChart.vue:59` |

Sizes are PyPI's wheel sizes and npm's unpacked sizes of each version (2026-11-23), not what each
adds to the install or the built page. pandas is the largest addition; yfinance requires it.

Computing values, weights, profit and loss, the change column and the rule checks is arithmetic
in the service's own code, with Python's `decimal`; decisions 4, 7 and 9 give the precedents for
what is computed.

## Advisories

Checked 2026-11-23 against the OSV database (`api.osv.dev/v1/querybatch`), at the versions above
and their new dependencies: PyPI yfinance 1.8.0, pandas 3.1.1, curl-cffi 0.17.0, cffi 2.1.1,
peewee 4.5.3, pytz 2026.6, python-dateutil 2.9.0.post0, tzdata 2026.2, python-socketio 5.18.1,
python-engineio 4.15.1, bidict 0.24.1, simple-websocket 1.1.0, wsproto 1.3.2; npm
socket.io-client 4.8.4, engine.io-client 6.6.8, socket.io-parser 4.2.7, engine.io-parser 5.2.3,
ws 8.21.0, xmlhttprequest-ssl 2.1.2, pinia 4.1.0, @tanstack/charts 1.5.0. None has a known
advisory. The versions the locks resolve are checked again once they are written, with an OSV check
of `uv.lock` and `npm audit` of `frontend/package-lock.json`.

bidict is MPL-2.0, a file-level licence that is not GPL or AGPL; it is used unmodified, as a
dependency of python-socketio.

Checked again 2026-11-24, after the locks were written. `uv.lock`, 149 packages, sent to OSV: no
advisory. Three resolved to other versions than listed above: python-dateutil 4.0.0, tzdata 2026.6,
and pycparser 3.12, which cffi brings in. `frontend/package-lock.json`, 594 versions, sent to OSV,
and `npm audit`: only the two advisories already known in the page's test tools, glob 13.0.7
(GHSA-3g3m-2fjr-6pw4) and minimatch 10.2.6 (GHSA-g3hv-75wg-m249), both under `@vue/test-utils`.
@tanstack/charts brings about 40 d3 modules (ISC), delaunator (ISC) and robust-predicates
(Unlicense); xmlhttprequest-ssl's licence is MIT in its own `package.json` and `LICENSE`.

## Decisions

### 1. One price source for every quote: Yahoo Finance through yfinance

**Decision**: the service gets every price from Yahoo Finance's public quotes through yfinance:
the Taiwan holdings (`.TW`), the US holdings, the Philadelphia Semiconductor index (`^SOX`), and
the US dollar in Taiwan dollars (`TWD=X`) to value the US holdings in Taiwan dollars. No key and no
account are needed. Each price is shown with the time it is from.

**Rationale**:
- The sample news's market tables were downloaded from the same Yahoo series, `.TW` and `^SOX`
  included (`data/truth/2026-09-16-fomc-raises-rate.md:38-39`), so the source is known to have
  every series the screen shows.
- Delay, from Yahoo's own table (`https://help.yahoo.com/kb/finance-for-web/sln2310.html`): the
  Taiwan Stock Exchange (`.TW`) 20 minutes; the Nasdaq Stock Exchange real time; Nasdaq Global Index
  Data Service, which carries the Philadelphia Semiconductor index, real time; currency rates
  (`=X`), from ICE Data Services, real time.
- yfinance's README says it is not affiliated with Yahoo, is meant for research and education, and
  that Yahoo's API is for personal use (`ranaroussi/yfinance@2492a853aee9:README.md:22-26`). The
  README of this repository says the same.

**Alternatives considered**:
- The Taiwan Stock Exchange's open data: daily figures after the close, not quotes during the day.
- twstock (MIT, PyPI 1.5.1, `mlouielu/twstock@942ea0a2558a:twstock/realtime.py:12-14`, `:73-95`):
  it asks the exchange's information page over plain HTTP, one request per poll, for Taiwan stocks
  only, so the US holdings would still need a second source. Who else depends on it was not found;
  no code search was available. Not used.
- An official, free, keyless real-time feed for Taiwan: none was found. The exchange sells real-time
  data to vendors (`https://www.twse.com.tw/pcversion/en/page/products/info-vendor/faq.html`).

### 2. Recent daily values first, then the live stream

**Decision**: when the service starts, before it takes requests, it reads each symbol's recent
daily series (`Ticker.history`, not adjusted for dividends), one symbol at a time and for at most
20 seconds, so the first page that opens has a value and a trading day for every price: the day's
close once it has ended, its latest price while it trades. Then it subscribes to yfinance's live
stream for all symbols at once and takes each message's symbol, price and time. The stream sends
the price as a binary float with a `price_hint`, the number of decimals to show
(`ranaroussi/yfinance@2492a853aee9:tests/test_live.py:18-21`); the service turns it into a
`Decimal` from its text and rounds it to that many decimals. A message without a symbol, price,
time or hint is dropped and counted, never guessed.

The change since the previous close is the stream's `change` when a message carries one, which is
against Yahoo's own previous close. Before that, it is against the close of the trading day before
the daily value. Yahoo's daily series has days with no close: in 006208.TW's, 2026-11-23 is `null`
while the next day's previous close, as Yahoo gives it for a one-day range (`chartPreviousClose`),
is 195.55, that day's close. yfinance drops such days by default (`keepna=False`; installed 1.8.0,
`yfinance/scrapers/history.py:145-147`, `:641-645`), so the day before them stood in and a two-day
move of +13.33% showed as one day's; Yahoo-side missing days are reported upstream too
(ranaroussi/yfinance issue 2621). The service reads the series with `keepna=True`, and when the day
before the latest value has no close, the previous close is not known: the change is missing for
that series and the strategy's change leaves it out and names it, as the totals do for a missing
price. It is never taken from an earlier day.

Outside the regular session the stream may still send prices. In the short runs below, NVIDIA had
prices at 13:17, 13:48 and 13:54 Taiwan time, past midnight in New York. Their `change` is against
the last regular close, so a US holding's change is then its move since that close, not the last
session's; in the second run NVIDIA went from the daily value 165.05 (+31.48% on 2026-11-23) to
164.22 (-0.50%), and the strategy's change went from 1,127,227 to 928,396 Taiwan dollars. The
strategy's change sums each holding against its own market's previous close, and the screen says
so. When a market sends nothing, its daily value stays, with its day.

When Yahoo cannot be reached, prices are missing, never zero (spec User Story 1, scenario 4). The
service waits at most 20 seconds for the daily series at start, then starts without them; it tells
the page whether its live connection is open, and the page says when prices are not following.
The stream is tried again every 3 seconds; a failure is said once in the terminal, and again only
after the stream has opened in between, so the terminal is not filled with the same line.

The stream is yfinance's synchronous `WebSocket` on a worker thread, not `AsyncWebSocket`. In
yfinance 1.8.0, `AsyncWebSocket.listen` does not reconnect after a dropped connection, because
`_connect()` does nothing while the old connection is still set, and after a normal close its loop
runs without awaiting and blocks the service (installed 1.8.0, `yfinance/live.py:141-200`). This
was reported and fixed upstream in pull request 3048, merged into the `dev` branch on 2026-11-18
(`ranaroussi/yfinance@581412edf5a0:yfinance/live.py:200-208`); as of 2026-11-24 no release has it,
and `dev` has diverged from 1.8.0, so no commit is pinned. The synchronous `listen` returns when the
connection ends (`yfinance/live.py:292-336`); the service then waits 3 seconds, opens a new
connection and subscribes again, the shape of that fix. While a connection is open, the service
sends the subscription again every 15 seconds with the same `subscribe`, as `AsyncWebSocket` does
(`yfinance/live.py:23`, `:76-93`) and the synchronous client does not. A yfinance release with the
fix would allow the asynchronous client again; that is a fact, not a plan.

Also:
- yfinance's time zone and cookie caches are kept in the service's local data folder
  (`set_tz_cache_location`, `yfinance/cache.py:637`), not in the user's own cache folder.
- The daily series are read one at a time. Read all at once, yfinance's cache database was locked
  for one symbol in the first short run against Yahoo ("database is locked"), which left it with no
  price.
- yfinance's own log is not shown: it logs every end of the stream as an error with a traceback,
  the service's own close at Ctrl+C included. The service logs a series it could not read, a
  stream that could not be opened or that ended, and how many recent prices it read at start.
- websockets 17 deprecates connecting without a context manager, as yfinance's synchronous client
  does, with a `DeprecationWarning`. The locked websockets 17.4 still supports it, and that one
  notice is filtered; a websockets release that drops it would stop the stream until yfinance
  changes.

**Rationale**:
- The precedent runs the same synchronous stream on a thread: `yf.WebSocket()`, `subscribe`, then
  `ws.listen(handler)` on a daemon thread
  (`marketcalls/YFinance-Alert-Manager@7f6df14d3e66:app.py:134-139`). It has no reconnect.
- The precedent pushes the stream to browsers over Socket.IO (same file, `:123`, `:134-139`).
- Reading recent closes with `Ticker.history` is how TradingAgents reads prices
  (`TauricResearch/TradingAgents@9fa1196fffbc:tradingagents/dataflows/vendors/yahoo/market.py:34`).
- The cost follows the prices that change, not the clock.

**Alternatives considered**:
- yfinance 1.8.0's `AsyncWebSocket`: it neither reconnects nor survives a normal close, as above.
- Pinning yfinance to the `dev` commit with the fix: `dev` has 20 commits 1.8.0 lacks and lacks 15
  that 1.8.0 has (GitHub compare `1.8.0...581412edf5`). Not used.
- Asking Yahoo for every price every few seconds: one request per symbol per poll, whether or not
  anything moved; TradingAgents wraps its Yahoo calls in retries and tests rate limits
  (`tradingagents/dataflows/vendors/yahoo/market.py:34`, `yf_retry`). Not used.

### 3. Socket.IO mounted inside the service, same origin only

**Decision**: a python-socketio `AsyncServer` in ASGI mode is mounted inside the FastAPI app at
`/socket.io`, so the app's Host check (`TrustedHostMiddleware`) also covers it. The allowed origins
are left at the default, which accepts only the origin of the request's own Host. One event,
`strategy`, carries the strategy the service recomputed (decision 4), sent when a price changes and
once to each page that connects. The page connects once, from one socket service, and keeps the
connection's state in a small Pinia store; each `strategy` event is checked with its zod schema and
written into the strategy query's cache, so the strategy has one copy in the page.

**Rationale**:
- Mounting the Socket.IO app inside FastAPI is open-webui's layout
  (`open-webui/open-webui@0666e59d26a4:backend/open_webui/main.py:812`;
  `backend/open_webui/socket/main.py:441-444`).
- python-engineio allows only the request's own scheme and Host when no origins are given
  (`miguelgrinberg/python-engineio@e86a9e7e4721:src/engineio/base_server.py:284-290`). The
  precedent's `cors_allowed_origins="*"` (`YFinance-Alert-Manager@7f6df14d3e66:app.py:16`) would let
  any web page in the browser read the stream; it is not followed.
- The frontend standards put live quotes on Socket.IO and server state in TanStack Query.
  Writing a pushed value into the query cache is TanStack Query's `setQueryData`, the same call
  that updates a query from outside a fetch.

### 4. The service computes every number

**Decision**: the service computes, with `decimal`, each holding's market value in Taiwan dollars,
its weight, its profit or loss in money and percent, the totals, the change since the previous
close, the donut's shares, the change column of a proposal and the rule checks. A US holding is
converted with the `TWD=X` rate; when that rate is missing, the US holdings are counted as missing,
never valued at a guessed rate. The profile keeps no rate from the day a US holding was bought, so
its cost is converted at the current rate as well: its profit is the price's move, not the
currency's, and the screen says the US holdings are valued at the latest rate. The page only draws
what it gets.

**Rationale**:
- The constitution, Principle IV: code computes the numbers in a diff, the model does not.
- Valuation fails closed when a conversion rate is missing in Vibe-Trading's portfolio
  (`HKUDS/Vibe-Trading@6ed378d:agent/src/portfolio/fx.py:1-7`, `:39-48`).

### 5. A simulated sample profile in the repository

**Decision**: `data/profile/sample.json` holds the sample: TSMC (2330), Delta Electronics (2308),
Yuanta Taiwan 50 (0050) and Fubon Taiwan 50 (006208) on the Taiwan Stock Exchange; NVIDIA and
Microsoft on Nasdaq; cash in Taiwan dollars; each with quantity and average cost; target weights;
and three rules. It is loaded into the database when its tables are empty, and labelled a
simulated sample, not investment advice.

**Rationale**:
- The four Taiwan symbols are the series of the sample news's market tables; NVIDIA and Microsoft
  are subjects of the sample news, so a revision question finds sources about them.
- Seeding from a JSON file in the repository and skipping rows already there is the retrieval
  template's way (`Azure-Samples/rag-postgres-openai-python@ecaafc4:src/backend/fastapi_app/setup_postgres_seeddata.py:22`,
  `:38-44`).

### 6. The split step also says whether the question asks for a revision

**Decision**: the split run (spec 007) returns one more field, `revise_strategy`, true when the
question asks to change the person's strategy. Only then is the answer run asked for the revised
strategy; every other answer streams as before. When the split fails, no proposal is asked for.

**Rationale**:
- A model reading the question picks the path and the code follows it in LlamaIndex's router
  (`run-llama/llama_index@25ce9e1:llama-index-core/llama_index/core/query_engine/router_query_engine.py:164`,
  `:187-195`).
- The split already runs once per question with tools off and a given JSON shape; one more field
  starts no extra program.

**Alternatives considered**:
- Asking every answer for the given shape with an empty proposal: Claude Code's answers would
  then never stream.
- A switch on the page: the spec has the person ask in the chat.

### 7. The answer and the proposal in one given shape; checked, never repaired

**Decision**: for a revision question, the answer run gets the retrieved sources and, as data, the
profile, the current targets, the rules and the latest prices (spec FR-009). It must return
`{"answer": text, "proposal": {"targets": [{"symbol", "percent"}], "reasons": [{"text", "sources"}]}}`,
`proposal` may be `null`. Claude Code's reply is read from `structured_output`; Codex's from the
file of `--output-schema` (spec 007 decision 5). The service checks the proposal: every holding
and `CASH` exactly once and nothing else, whole percents from 0 to 100 that add up to 100, source
numbers that exist. A proposal that fails is refused with the reason and never shown or repaired.
The answer text is shown either way; it arrives whole, and the page types it out as it does
Codex's answers. Until it arrives, the waiting line says the program is writing the answer and a
proposal (spec FR-011); the stream's context event says a proposal is expected, so the page knows
which line to show.

**Alternatives considered**:
- Streaming the answer as usual, then starting the program once more only for the proposal. The
  answer would start sooner, but every revision question would start the program a third time
  (after the split and the answer), with its own wait and its own use of the person's plan; in the
  second round of real runs one answer run took 30 to 107 seconds. And the proposal would come from
  a run that did not write the answer. Not used; the cost is a wait with no words, stated on screen.

**Rationale**:
- Both programs document a given output shape (spec 007 decision 5); Vibe-Trading constrains
  Claude Code's output the same way (`HKUDS/Vibe-Trading@84af312:agent/src/providers/claude_cli.py:289-290`).
- Whole percents give targets a person reads at a glance and make "adds up to 100" exact.
- The current, proposed and change columns follow Vibe-Trading's rebalance table
  (`HKUDS/Vibe-Trading@6ed378d:frontend/src/components/portfolio/RebalanceProposal.tsx:30`).

### 8. Accept and reject by the proposal's number

**Decision**: the service keeps each proposal with its question, program, time and status. The
page accepts or rejects by the proposal's number, with
`POST /strategy/proposals/{id}/decision` and the JSON body `{"decision": "accept"}` or
`{"decision": "reject"}`; the service applies the targets it stored, never
targets the page sends. Only the open proposal can be accepted; a new one replaces it, and the old
one is marked replaced. The answering programs have no way to accept.

**Rationale**:
- The person confirms in the chat's proposal card and the card closes once confirmed
  (`HKUDS/Vibe-Trading@6ed378d:frontend/src/components/chat/MandateProposalCard.tsx:11`, `:175-185`).
- The program proposes, the person decides: the constitution, Principle IV.

### 9. Rule kinds are the weight limits optimisers take, checked on target weights

**Decision**: three kinds, each with a limit in percent and an on or off switch: the most any one
holding may weigh; the least any held holding may weigh; the most one market (Taiwan or US) may
weigh. They are checked against the target weights of the current strategy and of a proposal;
the screen says so.

**Rationale**:
- PyPortfolioOpt (MIT) takes a minimum and a maximum weight for each asset
  (`PyPortfolio/PyPortfolioOpt@a6638d2e06da:pypfopt/base/_base_optimizer.py:173`, `:181-184`,
  `:221`) and lower and upper limits on a group's total (`add_sector_constraints`, `:398`,
  `:432-437`). These are limits on the weights being chosen, that is, on targets.
- Market value and actual weights move with prices; checking them would be rebalancing, which the
  spec does not list.

### 10. Layout: the chat page's strategy panel

**Decision**: the chat page becomes one dashboard group: the chat column as the main panel, the
strategy panel beside it and resizable, and in a narrow window the strategy panel moves into a
slide-over that the proposal card opens. This is task T018 of feature 003, done here.

**Rationale**: spec 003 research decision 5 already chose this layout and cites it.

### 11. The page's data layer

**Decision**: as spec 003 research decision 0: zod schemas for the strategy, rules, proposal and
the `strategy` event; contract routes `GET /strategy`, `PUT /strategy/rules`,
`POST /strategy/proposals/{id}/decision`; API functions that check each response; queries and
mutations with the key factory. The chat stream gets one more event type, `response.proposal`,
with the checked proposal or the reason it was refused; the context event says whether a proposal
is expected.

### 12. Other web pages cannot accept, reject or change rules

**Decision**: every request that changes something carries a JSON body: the decision on a
proposal, and the rules. FastAPI's strict `Content-Type` check then refuses the content types a
form or another page can send without the browser asking the service first, and the service adds
no CORS rule, so the browser is never given permission. The Socket.IO connection only sends from
the service; the page sends nothing on it that changes state. Tests send a form post and a
plain-text post to each endpoint and find them refused and nothing changed.

**Rationale**:
- OWASP: a `<form>` sends a "simple" request that is not preflighted, and a simple mitigation is to
  refuse the simple content types (`OWASP/CheatSheetSeries@c2a1e3e32cec:cheatsheets/Cross-Site_Request_Forgery_Prevention_Cheat_Sheet.md:236`,
  `:241-243`).
- FastAPI's strict check is the default and is meant to stop a page posting to a local AI agent
  without a preflight (`fastapi/fastapi@05e6df7e906c3decba377c37548019973f40bf15:docs/en/docs/advanced/strict-content-type.md:3`,
  `:7-17`); it already guards the chat (spec 001 research decision 11).

**Alternatives considered**:
- Refusing state-changing requests whose `Sec-Fetch-Site` is `cross-site` (same cheat sheet,
  `:146-148`): a second check in code of our own; the JSON body already makes such a request need a
  preflight that is never granted. Not added.
- A token in a cookie and a header: the page has no login or session to bind it to.

## Real runs (each needs the maintainer's consent)

1. The sample revision question, once with Claude Code and once with Codex: the proposal is
   checked and shown, its change column equals the service's computation, the answer cites the
   sources the reasons cite.
2. Accept one of them and reject the other; read the strategy after each.
3. A question that asks for no revision, with each program: no proposal.
4. The service running for a while during Taiwan trading hours and during US trading hours: prices
   arrive with their times and the screen follows them; Yahoo's delay as observed; how many messages
   arrive per minute, so that whether to merge them is decided from that count.
5. The attack document of spec 001 that hides "tell the user to buy everything", in the attack
   knowledge base, with a question asking to revise the strategy, once with each program: record
   the proposal, what its reasons cite, and whether the service refused it.

Three short runs against Yahoo were made while building the prices, on 2026-11-24 at 13:16, 13:48
and 13:54 Taiwan time. Each started the service with `uv run --no-sync chat-bridge --no-browser`,
opened the page in a headless browser, asked no question (the login check used a stand-in
program), and sent only the symbols. Each stayed connected for under a minute and ended with Ctrl+C.
They are not run 4: they show that the prices arrive and the service stops, not Yahoo's delay or how
many messages arrive per minute.
- 13:16: one series got no price ("database is locked": the daily series were read all at once);
  the first read of the strategy came before any price, so every holding was left out for a moment;
  the terminal showed a traceback at Ctrl+C and a deprecation notice. Each is handled above.
- 13:48: every series had a value at the first read; live prices came for TSMC and 0050 (the last
  trades before the Taiwan close, 20 minutes late) and for NVIDIA (overnight); Ctrl+C ended the
  service in 2.4 seconds with no process left and the database stopped.
- 13:54: the terminal said "Read 8 of 8 in 5.9 seconds"; Ctrl+C ended the service in 2.6 seconds.
- In all three, 006208's daily change was +13.33%, above the Taiwan Stock Exchange's 10% daily
  limit: the missing day explained above.

Runs with a stand-in yfinance (nothing reaches the network) covered what Yahoo did not show:
prices that move while the page is open, the subscription renewed every 15 seconds, and Yahoo out
of reach (each daily read times out, the stream cannot be opened): the service started after 20
seconds with every price missing, the page said it was not connected to the price source, the
chat still answered, and the stream's failure was said once.

In one of those runs Ctrl+C did not stop the service: the log ends at uvicorn's "Shutting down",
after asyncio had logged a `ConnectionResetError` from the headless browser's connection, closed
without a close frame when the browser was killed. In Python 3.13's proactor loop,
`_call_connection_lost` calls `sock.shutdown()` before it detaches the connection from the server
(`asyncio/proactor_events.py`); when that raises, the connection stays counted, and
`Server.wait_closed()` (`asyncio/base_events.py:390-412`), which uvicorn awaits before the
application's shutdown, never returns. uvicorn bounds that wait with its graceful-shutdown timeout,
which the service now sets to 5 seconds (`timeout_graceful_shutdown`; uvicorn 0.54.0
`uvicorn/server.py`, `shutdown` and `_wait_tasks_to_complete`). uvicorn's default is no limit; the
documented default of gunicorn, a server that drains production traffic, is 30 seconds. Five is
this service's own choice, not taken from either: one person stops this local service at a
terminal, and pressing Ctrl+C means stop. With no open answer the service ends in about two
seconds; an answer still coming in is cut five seconds after Ctrl+C (below); a connection that
never ends no longer keeps it running. A longer wait would look like a frozen terminal.

A connection reset sent on purpose was handled cleanly, so the browser case could not be made to
happen again. A request whose body never finishes keeps a connection open the same way: with it,
Ctrl+C ended the service in 6.7 seconds, uvicorn logging "Cancel 1 running task(s), timeout
graceful shutdown exceeded" and a `CancelledError` traceback for that request, then the
application's shutdown, which stopped the database; without the limit, the service was still
running 60 seconds after Ctrl+C.

The limit changes what Ctrl+C does to an answer still coming in. Measured with a stand-in program
whose answer takes 30 seconds, the page kept open until the service's process had ended:
- Without the limit, the answer went on to its end, was recorded whole, and the service ended 30
  seconds after Ctrl+C.
- With the limit, the answer stopped about five seconds after Ctrl+C and the service ended about
  seven seconds after it. In the first such run the question was not recorded at all: uvicorn
  cancels the request and goes on to the application's shutdown without waiting for it, and the
  service stopped the database before the cancelled answer wrote its record. The service now waits
  up to five seconds for the answers still being written before it stops the database
  (`finish_answers` in the chat service), and the question is recorded with the part that had
  arrived and "the client went away before the answer ended". The page says it cannot reach the
  chat service. The terminal shows uvicorn's traceback for the cancelled request and, after the
  service has ended, three "Exception ignored ... I/O operation on closed pipe" messages for the
  stopped program's pipes.

An earlier comparison found no difference with and without the limit. It was wrong: the script
that measured it closed the browser as soon as the service's port closed, which is at once on
Ctrl+C, and that closed connection is what cut the answer.
