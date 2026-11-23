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
  Data Service, which carries the Philadelphia Semiconductor index, real time.
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

### 2. Recent closes first, then the live stream

**Decision**: when the service starts, it reads each symbol's recent daily closes once
(`Ticker.history`), so every price has a value and a date from the start; then it subscribes to
yfinance's live stream (`AsyncWebSocket`) for all symbols at once and takes each message's symbol,
price and time. Outside trading hours the stream sends nothing for that market, so the screen shows
the last close with its date. When Yahoo cannot be reached, prices are missing, never zero
(spec User Story 1, scenario 4).

**Rationale**:
- yfinance's live stream is a push: one connection, each message a decoded quote with `id`,
  `price` and `time` (`ranaroussi/yfinance@2492a853aee9:yfinance/pricing.proto:4-6`,
  `yfinance/live.py:25-31`, `:141-200`); it resubscribes every 15 seconds and, with its default
  setting that logs errors instead of raising them, reconnects after a dropped connection
  (`live.py:23`, `:76`, `:188-200`; `yfinance/config.py:34`).
- The precedent pushes the same stream to browsers over Socket.IO
  (`marketcalls/YFinance-Alert-Manager@7f6df14d3e66:app.py:123`, `:134-139`).
- Reading recent closes with `Ticker.history` is how TradingAgents reads prices
  (`TauricResearch/TradingAgents@9fa1196fffbc:tradingagents/dataflows/vendors/yahoo/market.py:34`).
- The cost follows the prices that change, not the clock.

**Alternatives considered**:
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
never valued at a guessed rate. The page only draws what it gets.

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
Codex's answers.

**Rationale**:
- Both programs document a given output shape (spec 007 decision 5); Vibe-Trading constrains
  Claude Code's output the same way (`HKUDS/Vibe-Trading@84af312:agent/src/providers/claude_cli.py:289-290`).
- Whole percents give targets a person reads at a glance and make "adds up to 100" exact.
- The current, proposed and change columns follow Vibe-Trading's rebalance table
  (`HKUDS/Vibe-Trading@6ed378d:frontend/src/components/portfolio/RebalanceProposal.tsx:30`).

### 8. Accept and reject by the proposal's number

**Decision**: the service keeps each proposal with its question, program, time and status. The
page accepts or rejects by the proposal's number; the service applies the targets it stored, never
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
`POST /strategy/proposals/{id}/accept`, `POST /strategy/proposals/{id}/reject`; API functions that
check each response; queries and mutations with the key factory. The chat stream gets one more
event, `proposal`, with the checked proposal, or `proposal_refused` with the reason.

## Real runs (each needs the maintainer's consent)

1. The sample revision question, once with Claude Code and once with Codex: the proposal is
   checked and shown, its change column equals the service's computation, the answer cites the
   sources the reasons cite.
2. Accept one of them and reject the other; read the strategy after each.
3. A question that asks for no revision, with each program: no proposal.
4. The service running for a while during Taiwan trading hours and during US trading hours: prices
   arrive with their times and the screen follows them; Yahoo's delay as observed.
