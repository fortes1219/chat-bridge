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

- [ ] T001 `chat_bridge/strategy/models.py`: `profile_holdings`, `strategy_targets`, `strategy_rules`, `strategy_proposals` in the knowledge base's `Base` (FR-001, FR-006).
- [ ] T002 `data/profile/sample.json` and `chat_bridge/strategy/sample.py`: the simulated sample (2330, 2308, 0050, 006208, NVDA, MSFT, cash), its targets and three rules, loaded when the tables are empty; `serve()` loads it after the knowledge base (FR-001; research.md decision 5).
- [ ] T003 `chat_bridge/strategy/proposal.py`: `PROPOSAL_SCHEMA`, the strict model, the refusal codes (not the shape, unknown holding, missing holding, percent out of range, not adding up to 100, unknown source number), store, replace the open one, accept, reject (FR-003, FR-004, FR-006; decisions 7, 8).
- [ ] T004 `chat_bridge/strategy/compute.py` (targets part): the current targets and a proposal's change column (FR-005).
- [ ] T005 `chat_bridge/strategy/router.py`: `GET /strategy` (targets, the open proposal, the sample notice), `POST /strategy/proposals/{id}/decision` with a JSON body; included in the app (FR-010; decision 12).
- [ ] T006 `chat_bridge/chat/split.py`, `split_prompt.md`: `revise_strategy` in the shape and in `SplitOutcome` (decision 6).
- [ ] T007 `chat_bridge/chat/service.py`, `schemas.py`, `revision_prompt.md`: for a revision question, the context says a proposal is expected; the answer run with the profile, targets and rules as data and `PROPOSAL_SCHEMA`; the answer sent as one piece; `response.proposal` with the checked proposal or the refusal; the record keeps it (FR-003, FR-004, FR-009, FR-011).
- [ ] T008 [P] Fast tests: each refusal reason; a valid proposal stored and shown; accept applies the stored targets and only for the open proposal; reject leaves the strategy; a new proposal replaces the open one; the split's new field; the answer flow with stand-in programs for both kinds of reply; a question that asks for no revision gets no proposal; a form post and a plain-text post to the decision endpoint are refused and the strategy is unchanged (SC-003, SC-004, SC-005, SC-007).
- [ ] T009 Page data layer: `service/schema/strategy.ts`, `service/contract/strategy.ts`, `service/api/strategy.ts`, `queries/use-strategy-query.ts`, `queries/use-strategy-mutations.ts`, keys; `response.proposal` in the chat event schema.
- [ ] T010 Layout (003 T018): `ChatPage.vue` as one dashboard group, the chat column as the main panel, the strategy panel resizable beside it, a slide-over in a narrow window, all behind the login check (decision 10).
- [ ] T011 `views/strategy/StrategyPanel.vue` with the current targets, `ProposalDiff` (current, proposed, change; reasons with source numbers; accept and reject), `SampleNotice`; `views/chat/components/ProposalCard.vue` opens the panel; the waiting line for a revision answer; both languages (FR-011).
- [ ] T012 [P] Page tests: the diff table from a fixed proposal; accept and reject call their mutations once and refresh the strategy; a refused proposal shows its reason and no table; the card opens the slide-over in a narrow window; the 003 layout tests that T018 left (003 T019's drawer part).
- [ ] T013 Checks (ruff, mypy, fast suite, slow suite in the container, `vue-tsc`, ESLint, Prettier, Vitest), `git ls-files --eol`; the file list and one commit message to the maintainer.

## Phase 2: Prices (US1, US5; P1 and P2)

- [ ] T014 Dependencies: yfinance, python-socketio; socket.io-client, pinia, @tanstack/charts at the research.md versions (asks for approval); OSV check of `uv.lock` and `npm audit` (research.md `## Advisories`).
- [ ] T015 `chat_bridge/strategy/prices.py` and `state.py`: `PriceBook`; the feed with recent closes then `AsyncWebSocket`, one lifespan task, a stand-in for tests; each price a `Decimal` rounded by its hint, a message missing a field dropped and counted; a missing price stays missing; holdings, targets and rules kept in memory and read again only after a write (FR-008; decisions 1, 2).
- [ ] T016 `chat_bridge/strategy/compute.py` (prices part): values in Taiwan dollars with the `TWD=X` rate, weights, profit or loss, totals, change since the previous close, donut shares, holdings left out, US holdings left out when the rate is missing (FR-002; decision 4). The revision answer's data gains the latest prices (FR-009).
- [ ] T017 `chat_bridge/strategy/realtime.py`: the Socket.IO server mounted at `/socket.io` inside the app, default origins; `strategy` on connect and on each price change (FR-008; decision 3).
- [ ] T018 [P] Fast tests: the arithmetic with fixed prices; a missing price and a missing rate; a float price rounded by its hint; a message without a hint dropped; the event on a price change with the stand-in feed, with no database read; a Socket.IO connection from another origin is refused; slow test: the view from the real database.
- [ ] T019 Page: `service/socket/manager.ts`, `stores/strategy-socket.ts` (connection state only), each `strategy` event checked and written into the strategy query's cache; `SummaryCards`, `AllocationDonut` (`UChart` donut), `HoldingsTable` (`UTable`), `QuotesColumn` with each price's time and the source's delay; both languages (US1, US5).
- [ ] T020 [P] Page tests: the five parts from a fixed view; a missing price drawn as missing, not zero; an event updates the cards and the donut; an invalid event is not drawn; the socket is closed when the panel goes away.
- [ ] T021 Checks as T013; the file list and one commit message.

## Phase 3: Rules (US4; P2)

- [ ] T022 `chat_bridge/strategy/compute.py` (rules part) and `router.py` `PUT /strategy/rules`: the three kinds as a table, checked on target weights; unknown kinds and limits outside 0 to 100 refused with a code; a proposal's rule results before and after (FR-007; decision 9).
- [ ] T023 Page: `RuleChecks` with "M of N rules met", pass or fail, the note that targets are checked, the editor (add, change, turn off, save), and the before and after columns in `ProposalDiff`.
- [ ] T024 [P] Tests: each kind passes and fails at its edge; a refused rule; checks recomputed on save; before and after on a proposal; a form post and a plain-text post to `PUT /strategy/rules` refused with the rules unchanged (SC-007); page tests for the editor.
- [ ] T025 Checks as T013; the file list and one commit message.

## Phase 4: README and real runs

- [ ] T026 `README.md`, `README_tzh.md`: the strategy screen; the source of prices, its delay and terms; the sample is simulated and not advice; what the answering programs can and cannot do with the profile.
- [ ] T027 Ask the maintainer for consent to the real runs of research.md, in one list.
- [ ] T028 Real run: the runs of research.md; record what the page showed and the times.
- [ ] T029 Checks as T013, OSV and `npm audit` again; the file list and one commit message.
