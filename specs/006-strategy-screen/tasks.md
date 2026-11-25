---
description: "Task list for the strategy screen beside the chat"
---

# Tasks: The strategy screen beside the chat

**Input**: Design documents from `specs/006-strategy-screen/`

**Prerequisites**: plan.md, spec.md, research.md (with its `## Packages` and `## Advisories`)

**Tests**: The constitution (VII) requires tests with every change in behaviour.
- Fast tests start no program and reach no network: stand-in programs, a stand-in price feed.
- Slow tests run in the container, on the real database, without a model and without the network.
- Page tests use a stand-in socket.
- Tasks marked "Real run" start the maintainer's own Claude Code or Codex, only with consent.

Each phase ends with its checks and one commit the maintainer makes; the next phase starts after it.

## Phase 1: Ask, see the difference, accept or reject (US2, US3; P1)

- [x] T001 `chat_bridge/strategy/models.py`: `profile_holdings`, `strategy_targets`, `strategy_rules`, `strategy_proposals` in the knowledge base's `Base` (FR-001, FR-006).
- [x] T002 `data/profile/sample.json` and `chat_bridge/strategy/sample.py`: the simulated sample (2330, 2308, 0050, 006208, NVDA, MSFT, cash), its targets and three rules, loaded when the tables are empty; `serve()` loads it after the knowledge base (FR-001; research.md decision 5).
- [x] T003 `chat_bridge/strategy/proposal.py`: `PROPOSAL_SCHEMA`, the strict model, the refusal codes (not the shape, unknown holding, repeated holding, missing holding, percent out of range, not adding up to 100, unknown source number); `store.py`: store, replace the open one, accept, reject (FR-003, FR-004, FR-006; decisions 7, 8). A proposal with no reason, or a reason with no source, is not the shape (spec User Story 2, scenario 3). A proposal whose targets are all the current ones is treated as no proposal: not kept, no difference shown (spec Edge Cases).
- [x] T004 `chat_bridge/strategy/compute.py` (targets part): the current targets and a proposal's change column (FR-005).
- [x] T005 `chat_bridge/strategy/router.py`: `GET /strategy` (targets, the open proposal, the sample notice), `POST /strategy/proposals/{id}/decision` with a JSON body; included in the app (FR-010; decision 12). `/strategy` is now the service's, so the web test that used it as an example of a page address uses `/a/later/page`.
- [x] T006 `chat_bridge/chat/split.py`, `split_prompt.md`: `revise_strategy` in the shape and in `SplitOutcome` (decision 6).
- [x] T007 `chat_bridge/chat/service.py`, `schemas.py`, `chat_bridge/strategy/revision.py`, `revision_prompt.md`: for a revision question, the context says a proposal is expected; the answer run with the profile, targets and rules as data and `PROPOSAL_SCHEMA`; the answer sent as one piece; `response.proposal` with the checked proposal or the refusal; the record keeps it (FR-003, FR-004, FR-009, FR-011).
- [x] T008 [P] Fast tests (`tests/strategy/`), and slow tests of the store in the container (`tests/strategy/test_store.py`): each refusal reason; a valid proposal stored and shown; accept applies the stored targets and only for the open proposal; reject leaves the strategy; a new proposal replaces the open one; the split's new field; the answer flow with stand-in programs for both kinds of reply; a question that asks for no revision gets no proposal; a form post and a plain-text post to the decision endpoint are refused and the strategy is unchanged (SC-003, SC-004, SC-005, SC-007).
- [x] T009 Page data layer: `service/schema/strategy.ts`, `service/contract/strategy.ts`, `service/api/strategy.ts`, `queries/use-strategy-query.ts`, `queries/use-strategy-mutations.ts`, keys; `response.proposal` in the chat event schema.
- [x] T010 Layout (003 T018): `ChatPage.vue` as one dashboard group, the chat column as the main panel, the strategy panel resizable beside it, a slide-over in a narrow window, all behind the login check (decision 10).
- [x] T011 `views/strategy/StrategyPanel.vue` with the current targets, `ProposalDiff` (current, proposed, change; reasons with source numbers; accept and reject), `SampleNotice`; `views/chat/components/ProposalCard.vue` opens the panel, and once its proposal is accepted, rejected or replaced says so with no button (spec Edge Cases); the waiting line for a revision answer; both languages (FR-011).
- [x] T012 [P] Page tests: the diff table from a fixed proposal; accept and reject call their mutations once and refresh the strategy; a refused proposal shows its reason and no table; the card opens the slide-over in a narrow window; the 003 layout tests that T018 left (003 T019's drawer part).
- [x] T013 Checks (ruff, mypy, fast suite, slow suite in the container, `vue-tsc`, ESLint, Prettier, Vitest), `git ls-files --eol`; the file list and one commit message to the maintainer.

## Phase 2: Prices (US1, US5; P1 and P2)

- [x] T014 Dependencies: yfinance, python-socketio; socket.io-client, pinia, @tanstack/charts at the research.md versions (asks for approval); OSV check of `uv.lock` and `npm audit` (research.md `## Advisories`, checked again after the locks were written).
- [x] T015 `chat_bridge/strategy/prices.py` and `state.py`: `PriceBook`; the feed with recent daily values, read one at a time before the service takes requests, then yfinance's synchronous `WebSocket` on a worker thread, opened again when it ends and renewed every 15 seconds (research.md decision 2: 1.8.0's `AsyncWebSocket` neither reconnects nor survives a normal close), one lifespan task, a stand-in for tests; each price a `Decimal` rounded by its hint, a message missing a field dropped and counted; a missing price stays missing; holdings, targets and rules kept in memory and read again only after a write (FR-008; decisions 1, 2).
- [x] T016 `chat_bridge/strategy/compute.py` (prices part): values in Taiwan dollars with the `TWD=X` rate, weights, profit or loss, totals, change since each holding's own previous close (a holding whose previous close is not known, such as after a day Yahoo has no close for, is left out of the change and named), donut shares, holdings left out, US holdings left out when the rate is missing (FR-002; decisions 2, 4). The revision answer's data gains the latest prices (FR-009).
- [x] T017 `chat_bridge/strategy/realtime.py`: the Socket.IO server mounted at `/socket.io` inside the app, default origins; `strategy` on connect and on each price change (FR-008; decision 3).
- [x] T018 [P] Fast tests: the arithmetic with fixed prices; a missing price and a missing rate; a float price rounded by its hint; a message without a hint dropped; the event on a price change with the stand-in feed, with no database read; a Socket.IO connection from another origin is refused; the stream opened again after it ends or fails to open, and its subscription renewed; slow test: the view from the real database.
- [x] T019 Page: `service/socket/manager.ts`, `stores/strategy-socket.ts` (connection state only), each `strategy` event checked and written into the strategy query's cache; `SummaryCards`, `AllocationDonut` (`UChart` donut), `HoldingsTable` (`UTable`), `QuotesColumn` with each price's time and the source's delay, and whether prices are following (the page's connection and the service's connection to the price source) and any update not drawn; both languages (US1, US5).
- [x] T020 [P] Page tests: the five parts from a fixed view; a missing price drawn as missing, not zero; an event updates the cards and the donut; an invalid event is not drawn; the socket is closed when the panel goes away. The panel's old targets table is replaced by the holdings table, which shows each target beside its actual weight (spec User Story 1, scenario 6).
- [x] T021 Checks as T013; the file list and one commit message.

## Phase 2 follow-up: Ctrl+C while an answer is coming in

The shutdown limit of Phase 2 left Ctrl+C during an answer cut at five seconds, with about 90 lines
in the terminal (research.md decision 13).

- [x] T030 Dependency: sse-starlette at the research.md version (asks for approval); OSV check (research.md `## Packages`, `## Advisories`).
- [x] T031 `chat_bridge/chat/router.py`: `/chat/stream` through sse-starlette's `EventSourceResponse`, the same events separated by a bare newline; on shutdown the answer is cut off and the stream ends with an `error` event; `chat_bridge/chat/programs.py`: one stop that ends a program and every process it started, which `claude_code.py` and `codex.py` both call (decision 13).
- [x] T032 [P] Tests: a shutdown cuts the answer off and the stream ends with the `error` event; the grace period stays below uvicorn's limit; for each program, a stop ends everything a `.cmd` launcher started (fails with the old stop); the stream's events unchanged.
- [x] T033 Checks as T013; Ctrl+C as a person (an answer coming in, no answer, a connection that never ends), with the record, the processes, the database and what the page says; the file list and one commit message.

## Phase 2 follow-up: a proposal not in the shape fails the whole answer

A real run of a revision question had one reason without a source. The reply was checked as one
shape, so the answer was dropped with the proposal and the person saw an error, where User Story 2,
scenario 4 shows the answer and says why the proposal was refused.

- [x] T034 `chat_bridge/strategy/proposal.py`: the answer and the proposal are read apart; a proposal not in the shape is refused with `not_the_shape` and the answer is shown; a reply with no answer still fails. `revision.py` passes the refusal to the proposal event.
- [x] T035 [P] Tests: a proposal not in the shape, a reason without a source among them, gives the answer and the `not_the_shape` refusal, and nothing is kept; a reply with no answer still fails after the context.
- [x] T036 Checks as T013; the file list and one commit message.

## Phase 3: Rules (US4; P2)

- [x] T022 `chat_bridge/strategy/compute.py` (rules part) and `router.py` `PUT /strategy/rules`: the three kinds as a table, checked on target weights; unknown kinds and limits outside 0 to 100 refused with a code; a proposal's rule results before and after (FR-007; decision 9). The refusal codes and saving the list are in `store.py`, beside the proposal's refusals.
- [x] T023 Page: `RuleChecks` with "M of N rules met", pass or fail, the note that targets are checked; `RuleEditor` (add, change, turn off, save) with `useRuleEditor` keeping the draft; `useRuleText` wording a rule and its result; the before and after columns in `ProposalDiff`.
- [x] T024 [P] Tests: each kind passes and fails at its edge; a refused rule; checks recomputed on save; before and after on a proposal; a form post and a plain-text post to `PUT /strategy/rules` refused with the rules unchanged (SC-007); page tests for the editor.
- [x] T025 Checks as T013; the file list and one commit message.

## Phase 4: README and real runs

- [ ] T026 `README.md`, `README_tzh.md`: the strategy screen; the source of prices, its delay and terms; the sample is simulated and not advice; what the answering programs can and cannot do with the profile.
- [ ] T027 Ask the maintainer for consent to the real runs of research.md, in one list.
- [ ] T028 Real run: the runs of research.md; record what the page showed and the times.
- [ ] T029 Checks as T013, OSV and `npm audit` again; the file list and one commit message.
