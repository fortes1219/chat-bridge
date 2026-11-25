# Tasks: Your own holdings

The feature is one commit, made by the maintainer.

- [x] T001 Service: `HoldingInput`, `HoldingsRequest`, `check_holdings`, `save_holdings`, `PUT /strategy/holdings`; only Taiwan and US listings, the bounds; the price feed follows the saved holdings (US1; FR-001 to FR-003).
- [x] T002 Model input: the strategy block, with the computed numbers, with every answered question; the answer prompt says what it is; the split is given the holdings (US2; FR-004).
- [x] T003 Tests: fast, each US1 scenario, the model input and the split's input; slow, the save on the real database.
- [x] T004 Page: the holdings editor beside the rules editor; the request in the contract; the targets' total when it is not 100%; the texts in both languages; page tests.
- [x] T005 README in both languages: changing the holdings, and what is not done (FR-006).
- [x] T006 Checks (ruff, mypy, fast suite, the slow suite once in the container, vue-tsc, ESLint, Prettier, Vitest), `git ls-files --eol`, OSV and `npm audit`; run as a person with a stand-in program; the file list and one commit message.
- [ ] T007 Real run (consent): after changing the holdings, one question that asks to revise the strategy and one that asks what the recent events mean for the holdings without naming them, with each program.
