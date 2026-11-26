# Implementation Plan: Collect new knowledge with a command

**Spec**: [spec.md](spec.md)

## Summary

`uv run chat-bridge collect <addresses or paths>` sorts what it is given: a path is a news file (or a
folder of them) whose market moves are collected; an address is fetched once, and what comes back is
read as a feed when it is one and as a page otherwise. Pages go through trafilatura, which keeps the
main text as Markdown with the title, site and date; feeds go through feedparser, and each item's
linked page is collected as a page. Each page is written to `local_data/collected/` with front
matter that `ingest` already reads. For a news file, the command works out each market's day 0 from
its `event_time` (or its date), reads the daily closes of the series listed in
`data/market_series.json` once for the span the files need, and writes the section
「當日與之後的行情」 and its data sources into the file.

## Technical Context

- Python; trafilatura and feedparser (new); ruamel.yaml (new) for the news files' front matter;
  markdown-it-py, yfinance and requests (already locked).
- The zones and FinMind's daily closes of `chat_bridge/strategy` (`history.py`,
  `taiwan_sources.py`), imported by module name.
- robots.txt with the standard library's `urllib.robotparser`, as trafilatura's own crawler reads it.
- Cost: one request per address and per feed item, spaced per site; for market moves, one Yahoo
  request per series for the whole run and one second-source request per series only when Yahoo
  lacks a day the run needs. Nothing is read per news file.

## Files

- `chat_bridge/collect/cli.py`: the `collect` subcommand, registered as the other commands are.
- `chat_bridge/collect/pages.py`: fetching under robots.txt and spacing, page or feed, extraction.
- `chat_bridge/collect/collected.py`: the collected file's name and front matter, unchanged pages
  left alone.
- `chat_bridge/collect/markets.py`: the series file, the sessions, day 0 from a moment and by date.
- `chat_bridge/collect/closes.py`: the closes of the series for a span; placeholder bars and sessions
  not ended left out; missing days from the second source.
- `chat_bridge/collect/moves.py`: the rows, notes and first line of the section.
- `chat_bridge/collect/news_files.py`: the section placed or replaced, the data sources in `sources`.
- `chat_bridge/strategy/taiwan_sources.py`: FinMind's daily closes from a given day, public.
- `data/market_series.json`: the markets and the nine series.
- `pyproject.toml`, `uv.lock`: trafilatura, feedparser, ruamel.yaml.
- `tests/collect/`: the scenarios with saved pages, a saved feed and stand-in closes; no network.
- `docs/truth_format.md` sections 1 and 7, `README.md`, `README_tzh.md`.
