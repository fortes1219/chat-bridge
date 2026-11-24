# Implementation Plan: The strategy screen beside the chat

**Branch**: `dev/rc-0.1.0` (feature directory `specs/006-strategy-screen/`) | **Date**: 2026-11-23 | **Spec**: [spec.md](spec.md)

## Summary

The chat page gets a strategy panel beside the chat. It shows a simulated sample profile: number
cards, an allocation donut, the holdings with profit and loss, a quotes column with each price's
time, and the checks of the person's own rules. When a question asks for the strategy to be
revised, the split step (spec 007) says so, the answering program returns the answer and a revised
strategy in one given JSON shape, the service checks it, and the panel shows current target,
proposed target and change for each holding and cash, with accept and reject. Prices come from
Yahoo Finance through yfinance, recent closes first and then its live stream, and reach the page
over Socket.IO with the strategy the service recomputed from them.

The work is cut so that "ask, see the difference, accept or reject" runs on its own first; prices,
then rules, follow. Each part is one commit.

## Technical Context

**Language/Version**: Python 3.13 (`requires-python = ">=3.11"`); TypeScript 6 on Vue 3.5.

**Primary Dependencies**: added: yfinance, python-socketio, and, after Phase 2, sse-starlette
(service); socket.io-client, pinia, @tanstack/charts (page). research.md `## Packages`.

**Storage**: the local PostgreSQL of the knowledge base, four new tables: `profile_holdings`
(symbol, name, market, currency, quantity, average cost; cash is the row `CASH`), `strategy_targets`
(symbol, whole percent), `strategy_rules` (kind, limit, market, on), `strategy_proposals` (question,
program, time, targets and reasons as JSON, status). Prices are kept in memory only.

**Testing**: fast tests start no program and reach no network: a stand-in price feed, stand-in
programs, and the database stubbed where the chat tests already stub it. Slow tests, in the
container, cover the tables, the seeding, and the arithmetic against the real database. Page tests
use a stand-in socket. Real runs need the maintainer's consent (research.md).

**Target Platform**: Windows, macOS, Linux; the page in a current browser.

**Project Type**: a command-line tool that starts a local web service and its page.

**Constraints**: the strategy screen is behind the login check of feature 003; the service
computes every number; nothing reaches the person's machine from the answering program; prices are
missing, never zero, when they cannot be had.

## Changes to earlier features

| Feature | What it says now | What changes |
|---|---|---|
| 007 split (FR-001, decision 5) | The split returns the parts. | It also returns `revise_strategy`, true when the question asks to change the strategy (research.md decision 6). |
| 001 / 004 answers | Claude Code's answer streams; Codex's arrives whole. | For a revision question both answers arrive whole, with the proposal (research.md decision 7). Other questions are unchanged. |
| 003 T018 | A resizable `StrategyPlace` that says the screen comes later. | Done here, with the strategy panel in that place (research.md decision 10). |
| 003 stream | Events `response.context` and `response.output_text.delta`. | One more, `response.proposal`, with the checked proposal or the reason it was refused. |
| 003 stream (research decision 1) | Sent through `fastapi.sse.EventSourceResponse`. | Sent through sse-starlette's `EventSourceResponse`, the same events, so Ctrl+C ends an open stream at once; an answer cut off that way ends with an `error` event, `answer_failed` (research.md decision 13). |

## Design

### Service: the `chat_bridge/strategy/` feature

- `models.py`: the four tables, in the knowledge base's `Base`, so a database built by another
  version is refused as before.
- `sample.py`: loads `data/profile/sample.json` into the tables when they are empty
  (research.md decision 5); `serve()` calls it after preparing the knowledge base.
- `prices.py`: a `PriceBook` (symbol to price, time, source) and the feed that fills it: recent
  daily values with `Ticker.history`, one symbol at a time and before the service takes requests,
  then yfinance's synchronous `WebSocket` on a worker thread for every symbol at once, opened again
  when it ends and its subscription renewed every 15 seconds (decisions 1, 2). The stream runs as
  one task in the app's lifespan and is replaced by a stand-in in tests. It calls back when a price
  changes.
- `compute.py`: from holdings, targets, rules and the price book, the strategy view: each holding's
  price and time, value in Taiwan dollars, weight, profit or loss; cash; totals; the change since
  the previous close; the donut's shares; how many holdings are left out for a missing price; each
  rule's result on the targets. Also the change column of a proposal and its rule results
  (decisions 4, 9). Decimal throughout; lookup tables for the rule kinds.
- `proposal.py`: the given JSON shape of the answer and proposal (`PROPOSAL_SCHEMA`), the strict
  pydantic model that checks it, and the checks with their refusal codes (decision 7). It reads no
  database, so every check is tested without one.
- `store.py`: reading the profile and the strategy; storing a proposal, replacing the open one,
  accepting and rejecting, with the proposal row locked for the decision (decision 8).
- `revision.py`, `revision_prompt.md`: the revision answer's rules, the profile as data for the
  program, one run for the answer and the proposal, and the proposal event.
- `state.py`: the holdings, targets, rules and open proposal read from the database once and kept
  in memory, read again only after something writes them (seeding, a kept or decided proposal,
  saved rules). A
  price change updates the price book and recomputes the view in memory; it reads nothing from the
  database, so its cost follows the number of holdings, not the number of quotes.
- `realtime.py`: the Socket.IO `AsyncServer`, mounted inside the app at `/socket.io`, default
  origins; on connect and on every price change it sends `strategy` with the view (decision 3). No
  merging of messages is set now: real run 4 counts the messages per minute first.
- `router.py`: `GET /strategy`; `PUT /strategy/rules`; `POST /strategy/proposals/{id}/decision`
  with `{"decision": "accept" | "reject"}`. Every request that changes something has a JSON body,
  so FastAPI's strict Content-Type check refuses form and plain-text posts (decision 12). Unknown
  rule kinds, limits outside 0 to 100, and a proposal that is not open are refused with a code.

### Service: changes in `chat_bridge/chat/`

- `split.py`, `split_prompt.md`: the split's shape gains `revise_strategy`; `SplitOutcome.revise`.
- `service.py`: when the split says revise, the answer run gets `revision_prompt.md`, the sources,
  and the profile, targets, rules and prices as data, and asks for `PROPOSAL_SCHEMA` through the
  program's `reply_in_shape`; the answer text is sent as one piece; then `response.proposal`. The
  record keeps the proposal or the refusal. The context event says whether a proposal is
  expected.
- `programs.py`, `claude_code.py`, `codex.py`: the run that returns a reply in a given shape was
  named for the split, `split_reply`; it now serves the revision answer too, so it is named
  `reply_in_shape`.
- `schemas.py`: the new event type and the context's `proposal_expected`.
- `sources.py`: the languages and the `Source` model, moved out of `schemas.py` so the strategy's
  schemas can use them without importing the chat's request and event shapes, which use the
  strategy's.

### Page

- `views/chat/ChatPage.vue`: the chat column and the strategy panel in one dashboard group; the
  strategy panel in a slide-over when narrow; both only after the login check.
- `views/strategy/`: `StrategyPanel.vue` (the panel), `components/` (`SummaryCards`,
  `AllocationDonut` with `UChart` type `donut`, `HoldingsTable` with `UTable`, `QuotesColumn`,
  `RuleChecks` with the rule editor, `ProposalDiff` with accept and reject, `SampleNotice`),
  `composables/` (`useStrategy`, `useProposalActions`, `useRuleEditor`).
- `views/chat/components/ProposalCard.vue`: the card in the answer that opens the panel.
- `views/chat/`: when the context says a proposal is expected, the waiting line says the program
  is writing the answer and a proposal, which will arrive at once (spec FR-011).
- `service/schema/strategy.ts`, `service/contract/strategy.ts`, `service/api/strategy.ts`;
  `queries/use-strategy-query.ts`, `queries/use-strategy-mutations.ts`; `queries/keys.ts` gains the
  strategy keys.
- `service/socket/manager.ts` (one connection, created on first use, closed when no view needs
  it), `stores/strategy-socket.ts` (connection state only); each `strategy` event is checked and
  written into the strategy query's cache.
- `i18n/`: every new text in both languages, at most three key levels.

### Tests and data

- `data/profile/sample.json`; fast tests for the arithmetic with fixed prices (values, weights,
  profit and loss, missing prices, the exchange rate missing), the rule checks, the proposal checks
  (each refusal reason), accept and reject, the split's new field, the answer flow with a stand-in
  program that returns a proposal, the Socket.IO event on a price change with a stand-in feed, a
  price change that reads nothing from the database, a float price rounded by its hint, and a form
  post and a plain-text post to each changing endpoint refused with nothing changed.
- Slow tests: the tables, seeding once, reading the view from the real database.
- Page tests: the panel's five parts from a fixed view; a missing price shown as missing; the
  proposal table and accept and reject; the `strategy` event updates the query cache; an invalid
  event is not drawn; the slide-over in a narrow window.

## Order of work (each step one commit)

1. Ask, see the difference, accept or reject: tables, sample, `GET /strategy` with targets,
   the split's new field, the proposal shape and checks, the answer flow and `response.proposal`,
   accept and reject, the layout (003 T018), the proposal card and the diff table.
2. Prices: the price book and feed, the computed view, Socket.IO, the cards, donut, holdings table
   and quotes column.
3. Rules: kinds and checks, the editor, before and after on a proposal.
4. README, checks, real runs.

## Constitution Check

| Principle | How this plan meets it |
|---|---|
| I. Ecosystem precedent | Every added package has a dependency declaration and a call site cited; advisories checked (research.md). |
| II. Clone and run | yfinance and python-socketio come with `uv run`; the page's packages with its build; no key. |
| III. Raw documents | The answering program gets retrieved passages and the profile data, not files. |
| IV. Untrusted content | The program hands back a proposal in a given shape; the service checks it and refuses, never repairs; only the person accepts, and no other web page can accept for them; the service fetches prices and computes the diff. |
| V. Feature-based | One `strategy` package in the service, one `views/strategy/` folder in the page; rule kinds and refusal reasons are tables. |
| VI. Cost | One live connection to Yahoo for all symbols; one push per price change; no scans. |
| VII. Tests | Fast, slow and page tests with each step; real runs listed. |
| VIII. Honest claims | The source, its delay and terms are stated; the sample is labelled simulated, not advice. |
| Frontend standards | Contract first, TanStack Query for server state, Socket.IO for quotes, Pinia only for the connection's state, Nuxt UI only, both languages. |

## Complexity Tracking

| Item | Why | Simpler option not taken |
|---|---|---|
| pandas comes in with yfinance | yfinance requires it | No other keyless source carries both markets live (research.md decision 1). |
