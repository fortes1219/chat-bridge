---
description: "Task list for off-topic questions retrieving nothing"
---

# Tasks: Off-topic questions retrieve nothing

**Input**: Design documents from `specs/002-off-topic-questions/`

**Prerequisites**: plan.md, spec.md, research.md

**Tests**: The constitution (VII) requires tests with every change in behaviour, so each story has
its test tasks. Slow tests run in the Docker container. No task starts Claude Code.

**Scope**: SC-001 covers the health question only; Traditional-only function words stay
unfiltered (plan.md, "Decided after the measurements").

## Format: `[ID] [P?] [Story] Description`

- **[P]**: can run in parallel (different files, no dependencies)
- **[Story]**: the user story from spec.md (US1 to US3)

## Phase 1: Setup

None. No new dependency, no new module.

---

## Phase 2: User Story 1 - An off-topic question is listed as unanswered (P1) 🎯 MVP

**Goal**: the health question retrieves nothing, gets the fixed reply, and is listed as unanswered.

- [ ] T001 [US1] In `query_clauses` in `chat_bridge/tokenizer.py`, filter the jieba words as MaxKB does: its 52 query stop words, jieba's own stop words, a frequency floor of 4.0 from `jieba.analyse.default_tfidf`, and a lone Han character joining a run only when it is not a stop word and scores at least 4.5. User words are matched first and are not filtered (FR-001 to FR-003; research.md §1)
- [ ] T002 [US1] In the same function, when no clause is left, use every word of the question, at most 20, leaving out "or" and words with no letter or digit (research.md §2)
- [ ] T003 [P] [US1] Fast tests in `tests/test_tokenizer.py`: the health question gives 爸爸, 年紀, 推薦, 保健品 and no "大 了"; a question of stop words only falls back to its words; change `test_a_run_of_single_han_characters_becomes_one_clause`, whose example run "說 了" now loses 了, to a run the filters keep
- [ ] T004 [US1] Slow test in `tests/search/test_off_topic.py`, on the 71 sample files: the health question returns no passage (US1 scenario 1)
- [ ] T005 [US1] Slow test in `tests/chat/test_records.py`: add `2026-11-06-national-stabilization-fund-enters.md` to the sample files; the health question gets the fixed reply, Claude Code is not started, and the question is in the unanswered list (US1 scenario 3, SC-002)

**Checkpoint**: T004 and T005 fail before T001 and pass after it.

---

## Phase 3: User Story 2 - On-topic questions find what they found before (P1)

**Goal**: no question loses the passages that answered it.

- [ ] T006 [P] [US2] Fast tests in `tests/test_tokenizer.py`: 台積電 and 0050 keep the name and their synonyms in the clauses (US2 scenario 4, FR-003)
- [ ] T007 [US2] Slow test in `tests/search/test_off_topic.py`: with a limit of 8, the Chinese Fed question keeps the files of 2026-06-17, 2026-08-28, 2026-09-16 and 2026-11-10, and the English one keeps 2026-06-17, 2026-07-29, 2026-08-28 and 2026-09-16 (US2 scenarios 1 and 2, SC-003)
- [ ] T008 [US2] Run the search-yield suite, `tests/search/test_yield.py`, unchanged; no number is lower than 55, 0, 25, 26, 2 (US2 scenario 3, SC-004)

---

## Phase 4: User Story 3 - The keyword query shows what was kept (P3)

- [ ] T009 [US3] Slow test in `tests/search/test_off_topic.py`: the query the search reports for the health question is `爸爸 or 年紀 or 推薦 or 保健品` (FR-006)

---

## Phase 5: Polish

- [ ] T010 [P] Rewrite the docstring of `query_clauses` in `chat_bridge/tokenizer.py`: it says the stop-word and frequency steps are not taken
- [ ] T011 [P] One line in the search section of `README.md` and `README_tzh.md`: the keyword query leaves out function words, very common words and lone common characters, using Simplified Chinese lists; a question that shares only common words with the data can still find passages
- [ ] T012 Checks: ruff and mypy; the fast suite on the host; the slow suite in the container (`docker compose -f compose.test.yml run --rm slow-tests`). Record the measurements for the three off-topic questions, the two Fed questions and the yield suite here, before and after (FR-008)
- [ ] T013 `git ls-files --eol` shows no `w/crlf`; give the maintainer the files grouped by kind, with one commit message per group

## Dependencies

- T001 before T002 to T009. T003 and T006 can run together.
- T004, T005, T007, T008 and T009 need the container.
