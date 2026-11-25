# Implementation Plan: Taiwan previous closes

**Spec**: [spec.md](spec.md)

## Summary

When the service reads the recent closes, it also reads each Taiwan series' daily closes and
ex-dividend results from FinMind, the advance notices of the markets it holds, the open-data
daily tables only for a series FinMind left without a previous close (spec FR-003), and, for a
series still without one, Yahoo's own quote. The price book keeps, for each series, the
previous close of each day those give, and every quote of that series, from Yahoo's daily series
or its live stream, takes the previous close of its own day from there. FinMind's latest close is
kept too, so a day Yahoo has not got yet is shown.

## Technical Context

- Python, requests (already locked), the price book and the price source of spec 006.
- Cost: two requests a Taiwan series at start and on a holdings change; nothing per price.

## Files

- `chat_bridge/strategy/prices.py`: reading the sources; the previous closes in the price book.
- `pyproject.toml`, `uv.lock`: requests declared.
- `tests/strategy/test_prices.py`: the scenarios.
- The panel's words (T003, its own commit): `frontend/src/i18n/`, the summary cards.
