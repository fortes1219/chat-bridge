# Implementation Plan: Prices looked up for the question

**Spec**: [spec.md](spec.md)

## Summary

The split's reply also names price lookups. The service checks them, reads the closes once a day
per symbol from the sources it already reads, while the sections are searched; it computes each
period's trend and, with the market section's own alignment, each found event's rows, and gives
the program a `<prices>` block in place of the market tables. The page shows what was looked up.
`ingest` keeps each file's timing and stores no market section; a knowledge base from before is
cleared and made again by the app itself when the service starts or `ingest` runs, and an index
built another way is rebuilt at the start. `truth` stops writing market sections, and `collect`
stops computing them.

## Technical Context

- Python 3.11 or later; pydantic, pandas, yfinance, requests, anyio, SQLAlchemy; Vue 3 with Nuxt UI
  and zod. All already installed.
- No package is added.
- Cost: no model run is added; the split's reply is a little longer. One Yahoo request per symbol
  and period not read within the day, and one FinMind request for a Taiwan symbol Yahoo lacks a day
  of, each at most 10 seconds, at once and during the search.

## Files

- `chat_bridge/price_history/` (new): from `collect/`, the closes reader, the markets file and the
  row computation; new, the lookups' checks, the day's store, the trend and the `<prices>` block.
- `chat_bridge/ingest/`: `markets` and `event_time` on the document; no market section stored, and
  the count of those left out in the report; an old knowledge base cleared and an old index
  rebuilt (`refresh_index`). `chat_bridge/database.py`: the differences of a given set of tables.
  `chat_bridge/chat/server.py`: the start refreshes the knowledge base before anything else.
- `chat_bridge/chat/split.py`, `split_prompt.md`: `prices` in the reply; the holdings and the
  listed series named for the program.
- `chat_bridge/chat/service.py`, `schemas.py`: the market-section exclusion and attachment removed;
  the reads during the search; `<prices>` in the input; the context's lookups; the record.
- `chat_bridge/chat/answer_prompt.md`, `chat_bridge/strategy/revision_prompt.md`.
- `chat_bridge/truth/`, `chat_bridge/collect/`: no market section written or computed.
- `frontend/src/service/schema/chat.ts`, `views/chat/components/`, the texts in both languages.
- `docs/truth_format.md`, `README.md`, `README_tzh.md`.
- Tests beside the chat, ingest, truth and collect tests and the page tests.

## Version

This release is 0.2.0. The version in `pyproject.toml` (and the project's entry in `uv.lock`) is
changed to 0.2.0 by the writer in a commit of its own, after the maintainer has merged 0.1.0 and
named the branch, before the first commit of this feature. The READMEs name no version.

## Commits

Two, each one behavior: the chat's lookup with the page and the knowledge base's change; then no
market section in new files.
