# Research: Your own holdings

## Packages

No package is added; each need is met by a package already in the project.

| Need | Package | Version | License | Size | Dependency declared in | Called in |
|---|---|---|---|---|---|---|
| Check the holdings the page sends: known fields only, amounts as decimals | pydantic | 2.14.3 | MIT | none added: already a dependency | `fastapi/full-stack-fastapi-template@77e550a:backend/pyproject.toml:10` | `Azure-Samples/rag-postgres-openai-python@ecaafc4:src/backend/fastapi_app/api_models.py:5`, `:93-97` |
| Replace the holdings and their targets in one transaction | SQLAlchemy | 2.0 | MIT | none added: already a dependency | `Azure-Samples/rag-postgres-openai-python@ecaafc4:src/backend/pyproject.toml:13` | `Azure-Samples/rag-postgres-openai-python@ecaafc4:src/backend/fastapi_app/postgres_models.py:4`, `:54` |
| Read the prices of the new holdings and follow them live | yfinance | 1.8.0 | Apache-2.0 | none added: already a dependency | `TauricResearch/TradingAgents@9fa1196fffbc:pyproject.toml:30` | `TauricResearch/TradingAgents@9fa1196fffbc:tradingagents/dataflows/vendors/yahoo/market.py:6`, `:34` |
| The editor on the panel: inputs, buttons | @nuxt/ui | 4.13.0 | MIT | none added: already a dependency | `nuxt-ui-templates/dashboard-vue@abfe4e74024a:package.json:14` | `nuxt-ui-templates/dashboard-vue@abfe4e74024a:src/components/home/HomeChart.vue:59` |
| The holdings request in the page's contract, checked before it is sent | zod | 4.6.7 | MIT | none added: already a dependency | `middleapi/orpc@26175d2:playgrounds/contract-first/package.json:23` | `middleapi/orpc@26175d2:playgrounds/contract-first/src/contract/sse.ts:2`, `:11` |
| Saving as a mutation: pending, error, the view replaced by the response | @tanstack/vue-query | 5.108 | MIT | none added: already a dependency | `middleapi/orpc@26175d2:playgrounds/nuxt/package.json:19` | `middleapi/orpc@26175d2:playgrounds/nuxt/app/plugins/vue-query.ts:10-23` |

## Advisories

None added: no package or version changes. The lock files are checked with OSV and `npm audit`
before delivery.

## Decisions

1. **The holdings are saved as the rules are.** One `PUT /strategy/holdings` with every holding
   in order replaces them, checked first, written in one transaction, answered with the strategy
   after it (spec 006, the rules editor). The page edits a copy and sends it on save.
2. **The market comes from the symbol, through a table; a symbol the table does not place is
   refused.** Vibe-Trading reads a listing's market from its Yahoo symbol with an ordered table of
   patterns, `.TW` and `.TWO` to Taiwan and a bare ticker of one to five letters to the US, and a
   market's currency from another table (HKUDS/Vibe-Trading@89c28d8, MIT,
   `agent/backtest/engines/_market_hooks.py:130-161`, `:268-273`, `:287-309`). Here the table has
   the two markets whose exchange rate and rules the service has. Vibe-Trading falls back to a
   default market for a symbol it cannot place (`:460`); here such a symbol is refused, as a
   guessed market would value it in the wrong currency without a word.
3. **Targets follow the holdings, nothing is guessed.** A kept holding keeps its target; a new one
   starts at 0%, since the person has not planned it; a removed one loses its target. When the
   targets then add up to other than 100%, the panel says so, and a revision proposal, which must
   add up to 100%, sets them again; only the person applies it. This reads the maintainer's
   requirement that the holdings can be changed at any time while a strategy takes effect only
   when the person applies it.
4. **An open proposal is closed as replaced.** It was checked against the holdings before the
   save, so accepting it would apply targets to holdings that changed.
5. **The model is given the holdings with every answered question.** A portfolio assistant puts
   the formatted holdings, with quantity, average cost, market value and gains, in front of every
   chat turn (investbrainapp/investbrain@6d76b32, CC BY-NC 4.0, read for its design only,
   `app/Ai/Agents/ChatWithPortfolioAgent.php:26-38`, `app/Models/Portfolio.php:238-253`).
   Here the programs run with their tools off, so the holdings go in as data, not as a tool the
   model calls. The values, weights and profit are the service's.
6. **The program that lists a question's parts is given the holdings.** Search queries are
   written by a model that is given the user's context: earlier messages in the Azure template
   (Azure-Samples/rag-postgres-openai-python@ecaafc4, MIT,
   `src/backend/fastapi_app/rag_advanced.py:110-116`), the user's name, location and memories in
   Khoj (khoj-ai/khoj@ae229ca, AGPL-3.0, read for its design only,
   `src/khoj/routers/helpers.py:1398-1442`). Here the split is given each holding's symbol and
   names, and writes a search for each when the question is about the user's holdings without
   naming them. Adding holdings to search queries was not found in the projects read. The split
   lists at most 8 searches, so with more than 8 holdings only 8 get one of their own.
7. **Bounds.** Every holding goes to the program with each question and has a live price
   subscription, so there are at most 30 besides cash; a name has at most 40 characters; an
   amount is at most 1e15.
8. **A symbol of the right form that Yahoo does not know is kept.** Asking Yahoo on every save
   would make saving wait on Yahoo; the panel already shows a holding without a price as missing
   and leaves it out of the totals.
