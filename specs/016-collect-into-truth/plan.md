# Implementation Plan: Collect makes truth files as the 71 were made

**Spec**: [spec.md](spec.md)

## Summary

Two commands, two feature packages. `collect` finds the events (from the channels, with the agent's
web search) or sorts given pages into events (the agent with no tool), reads every page once, and
stores each event in `local_data/collected/<event_date>-<12 hex>/`. `truth` reads only the stored
events and makes each into a file of `docs/truth_format.md` in `data/truth` (or `--into`):

1. **Writing.** For each event, the agent with no tool gets the format, the vocabulary, one file of
   the folder as an example, the folder's files of the event's date, and the stored pages' text as
   data, and answers with a record in a JSON schema: front matter values, items with source id and
   passage, notes, the significance reason, the number conversions, or the name of the folder's
   file that already is this event.
2. **Program checks.** Each passage is in its stored page; each item is in its source's language;
   ids, targets, exposure words, markets, significance, `event_time`, the file name and the asked
   dates are as listed; no quantity is left written with 萬, 億, 兆 or 碼 after a numeral; each
   conversion's original is in its page and its result in the file. A record that fails goes back
   to the agent once with the reasons; when it fails again the event stays stored for the next run.
3. **File.** The file is written in the 71 files' layout; feature 013's code adds the market section
   from one read of the daily closes; it goes into the folder whole (written beside its name and
   renamed onto it), the conversions into `tests/data/number_conversions.md` when the folder is
   `data/truth` (shown in the terminal otherwise), and the event's stored folder is removed.
4. **No ingest.** `truth` ends with `uv run chat-bridge ingest <folder>` when it wrote a file.

At most `--workers` events (5 by default) are under way at once; `--limit N` makes only the first N.

## Technical Context

- Python; no new package. trafilatura, feedparser and ruamel.yaml as feature 013 uses them; the
  programs as the chat starts them (`web_reply_in_shape` for the search, `reply_in_shape` with no
  tool for the sorting and the writing). `asyncio.Semaphore` bounds the events under way.
- The rules are read from `docs/truth_format.md` (the collection targets: the numbered list after
  「採集目標」; the sections: section 二's `` `## …` `` lines, 「（可省）」 marking the optional one;
  the front matter keys: section 一's table), `docs/exposure_vocabulary.md` (each `` - `word`： ``
  line) and `data/market_series.json` (the market codes). A doc that yields none of them, or a key
  the program does not write, stops the command and names the doc.
- The record's JSON schema is built from those rules: the targets, the exposure words, the markets,
  the headings, the source ids and the folder's files of the date are enums, so the agent is held
  to them and the program checks them again.
- Passages are compared with runs of white space made one space. The stored page text given to the
  agent is the same text the passages are looked for in.
- The number rule: 萬, 億, 兆 or 碼 right after an Arabic digit, a full-width digit, or one of
  〇零一二兩三四五六七八九十百千半, in the title or an item; keyword groups are not checked (section 一).
- The language rule: an item citing a source whose `lang` starts with `zh` has a Han character; one
  citing a source in another language has none.
- Cost: `collect` one model run, and one request per page and per site's robots.txt, spaced 5
  seconds per site; `truth` one model run per stored event, two when its first record fails, at most
  `--workers` at once, each with the chat's time limit, and one read of the daily closes. The truth
  folder is read only for its files dated on or after the earliest stored event (by their names).

## Files

- `chat_bridge/collect/`: `cli.py` (`collect`: from the channels, from addresses, and the market
  moves of news files as before), `store.py` (the stored events: a folder named from the date and
  the pages, written whole, read back, removed only when it is a stored event of the collected
  folder), `channels.py` and `channels_prompt.md` (the search, told the truth folder's events and
  the stored ones), `grouping.py` and `grouping_prompt.md`, `pages.py` (pages and feeds read into
  plain text; a redirect to another site read only when that site's robots.txt allows it), and the
  market section's modules (`markets`, `closes`, `moves`, `news_files`, `service`).
- `chat_bridge/truth/` (new feature package): `cli.py` (`truth`, with `--into`, `--limit`,
  `--workers`), `maker.py` (one stored event to a file), `record.py` and `writing_prompt.md` (the
  schema, the question and the checks), `rules.py`, `truth_files.py` (the folder's files, the file
  name, the 71 files' layout, the record of conversions).
- Removed: `chat_bridge/collect/checking.py` and `checking_prompt.md` (the second reader).
- `tests/collect/` (the store, `collect` with stand-ins) and `tests/truth/` (the rules, the checks,
  the layout, `truth` with stand-ins: the runs at once, a stop, the cleanup).
- `README.md`, `README_tzh.md`, `docs/truth_format.md` (its header and section 7's command line).
