# Implementation Plan: Off-topic questions retrieve nothing

**Branch**: `dev/rc-0.1.0` (feature directory `specs/002-off-topic-questions/`) | **Date**: 2026-11-20 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `specs/002-off-topic-questions/spec.md`

## Summary

The keyword query drops words that carry no meaning, with the filters of the project the search
already follows (MaxKB's `to_query`, updated): its query stop words, a floor on jieba's inverse
document frequency, and its rule for lone characters. The knowledge base's own words are matched
first and are never filtered. Nothing else changes: not the index, the vector side, the fusion, nor
the `search` command.

Measured in the container, this brings the health question from 1 passage to 0 and changes no
on-topic result and no yield number. It does not bring the world-cup or the vitamins question to 0.
The two precedents that do (a keyword-score floor, every word required) each lower the yield, so
they are not adopted. The numbers are in [research.md](research.md).

**Decided after the measurements** (the spec was changed to match):

- SC-001 keeps the health question only (1 passage → 0). The world-cup and the vitamins question
  are known limits: no precedent brings them to 0 without lowering a yield number. A keyword-score
  floor of 0.6 takes 0050 to 0 and the yield from 55 to 52. Requiring every word takes the yield
  from 55 to 50.
- Traditional Chinese: the gap is accepted. Function words written the same in both scripts are
  filtered. Traditional-only forms (這, 嗎, 什麼, 我們) are not. No OpenCC, no re-ingest; FR-004
  stands. Converting would not have changed the world-cup result: the Simplified forms still score
  above the 4.0 floor (资料 5.86, 规则 6.55, 这次 5.48).
- When every word is filtered out, every word of the question is searched, as MaxKB does
  (research.md §2) and as the search does today.

## Technical Context

**Language/Version**: Python 3.13 (`requires-python = ">=3.11"`)

**Primary Dependencies**: jieba, already locked. Its `jieba.analyse` module carries the frequency
table and its own stop words. No new dependency.

**Storage**: No change. Nothing is re-ingested (FR-004).

**Testing**: pytest. The fast tests for the clauses run on the host; the search and chat tests run
in the Docker container. ruff and mypy (strict) with the existing settings.

**Target Platform**: The user's own computer: Windows, macOS or Linux.

**Project Type**: A command-line tool that also starts a local web service.

**Performance Goals**: The frequency table loads once per process, as in MaxKB.

**Constraints**: Query side only. The vector side, its threshold and the fusion stay as they are
(FR-005).

**Scale/Scope**: One function, `query_clauses`, and its tests.

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-check after Phase 1 design.*

| Principle | How this plan meets it |
|---|---|
| I. Ecosystem Precedent First | Every filter is MaxKB's, with commit and lines (research.md §1, §2). The two precedents not adopted are measured (§3, §4). Traditional Chinese has no precedent short of converting both sides; the gap is stated, not patched with an invented rule (§5). |
| II. Clone and Run | No new dependency, no new step. |
| III. The Model Sees Only Retrieved Passages | Unchanged. Fewer unrelated passages reach the model. |
| IV. Untrusted Content Stays Data | Unchanged. |
| V. Feature-Based Structure and Clean Code | The change stays in `chat_bridge/tokenizer.py`, beside the steps it already takes from MaxKB. The stop words and limits are named constants. |
| VI. Cost Follows the Work | One table load per process; each question costs a few dictionary lookups. |
| VII. Tests Prove What the User Gets | A fast test per filter on the clauses. Slow tests on the 71 sample files: the health question finds nothing, both Fed questions keep their files, the yield suite holds. A slow chat test: the health question gets the fixed reply and is listed as unanswered. |
| VIII. Honest Claims | The README states which questions still find passages and why. |
| Repository Hygiene | English, LF; no machine details. |

Result: passes.

## Project Structure

### Documentation (this feature)

```text
specs/002-off-topic-questions/
├── spec.md
├── plan.md        # This file
├── research.md    # Measurements and decisions
└── tasks.md
```

### Source Code (repository root)

```text
chat_bridge/
└── tokenizer.py           # query_clauses: MaxKB's stop words, frequency floor, lone-character rule, fallback

tests/
├── test_tokenizer.py      # Fast: each filter on the clauses
├── search/
│   └── test_off_topic.py  # Slow: the health question, the Fed questions
└── chat/
    └── test_records.py    # Slow: the health question is listed as unanswered

README.md, README_tzh.md   # What the keyword query leaves out, and what it still finds
```

**Structure Decision**: The keyword query is built in one function, `query_clauses`, which already
follows MaxKB's `to_query`. The filters go there. The search module keeps calling it as it does.

## Complexity Tracking

None.
