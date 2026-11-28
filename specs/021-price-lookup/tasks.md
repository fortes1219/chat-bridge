# Tasks: Prices looked up for the question

Two commits, made by the maintainer, once the maintainer has read the spec.

## The chat looks prices up

- [ ] T000 The version: `pyproject.toml` and `uv.lock` to 0.2.0, a commit of its own, once the maintainer has merged 0.1.0 and named the branch.
- [x] T001 Before any code (no model): replay the 26 recorded cases, the 9 market questions and the holdings splits without market sections, with the stand-in lookups (research, decision 8): the input's characters, the `<prices>` block's size, the holdings question's in particular, how many of its events' rows fit in the bound and how many do not, how many sections each market question's own search finds, and the read time; report, and settle the row's columns and the bound, before any code.
- [x] T002 `chat_bridge/price_history/`: move the closes reader, the markets file and the row computation from `collect/`; the lookups' checks (FR-002), the day's store (FR-006), the trend and the rows (FR-003), the block and its bound (FR-004, FR-005).
- [x] T003 SC-002: the 71 files' tables against the service's rows.
- [x] T004 `ingest`: `markets` and `event_time` on the document (FR-011); no market section stored, and the count of those left out in the report (FR-008).
- [x] T005 Split: `prices` in the reply and the prompt (FR-001).
- [x] T006 Chat: the market-section exclusion and attachment removed (FR-008); a question about prices alone still split (FR-015); the reads during the search (FR-007); `<prices>` in the input; the context (FR-010); the record (FR-013); the two prompts (FR-009).
- [x] T007 Page: the prices line in both languages (US 2).
- [x] T008 Tests (SC-001); checks (ruff, ruff format, mypy, fast suite, vue-tsc, ESLint, Prettier, Vitest, build), `git ls-files --eol`; the replay again (SC-003); the slow suite once, at the end.
- [x] T009 As a person, with a stand-in program and stand-in prices (SC-004).
- [ ] T010 Real run (consent; SC-005): the number of model runs stated before asking.
- [ ] T011 `README.md`, `README_tzh.md` (FR-014); the file list and one commit message.

## New news files carry no market table

- [ ] T012 `truth` and `collect`: no market section (FR-012); the tests of the retired behavior deleted; `docs/truth_format.md` (FR-014); checks; the file list and one commit message.
