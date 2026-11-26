# Implementation Plan: Collect makes truth files as the 71 were made

**Spec**: [spec.md](spec.md)

## Summary

`collect` stops writing collected pages of its own format. From the channels, or from web
addresses, it ends in files of `docs/truth_format.md` in `data/truth` (or `--into`), one per
event:

1. **Events.** From the channels, the person's own agent (web search and web reading, as feature
   015 starts it) lists the events on the collection targets between the folder's latest event date
   and `--until`, each with its source pages on the channels, and is told the events the folder
   already has. From addresses, the command reads the pages first and the agent, with no tool,
   sorts them into events.
2. **Pages.** The command reads each source page itself (robots.txt, the wait per site, trafilatura's
   limits), as plain text.
3. **Writing.** For each event, the agent with no tool gets the format, the vocabulary, one file of
   the folder as an example, and the pages' text as data, and answers with a record in a JSON
   schema: front matter values, items with source id and passage, notes, the significance reason,
   the number conversions.
4. **Program checks.** Each passage is in its page; each item is in its source's language; ids,
   targets, exposure words, markets, significance, `event_time`, the file name and the date window
   are as listed; no quantity is left written with 萬, 億, 兆 or 碼 after a numeral; each
   conversion's original is in its page and its result in the file.
5. **Second reader.** Another run of the agent, with no tool and only the items, notes and passages,
   answers item by item whether each says only what its passage says. A record that fails step 4
   or 5 goes back to the writing run once with the reasons, and is refused when it fails again.
6. **File.** The file is written in the 71 files' layout; feature 013's code adds the market section
   from one read of the daily closes; then it goes into the folder whole (written beside its name
   and renamed onto it), and the conversions into `tests/data/number_conversions.md` when the
   folder is `data/truth`, shown in the terminal otherwise.
7. **No ingest.** The command ends with `uv run chat-bridge ingest <folder>`.

A refused event is named with its reason and the run goes on to the next; nothing half made goes
into the folder.

## Technical Context

- Python; no new package. trafilatura, feedparser and ruamel.yaml as feature 013 uses them; the
  programs as the chat starts them (`reply_in_shape` with no tool, `web_reply_in_shape` for the
  search).
- The rules are read from `docs/truth_format.md` (the collection targets: the numbered list after
  「採集目標」; the sections: section 二's `` `## …` `` lines, 「（可省）」 marking the optional one;
  the front matter keys: section 一's table), `docs/exposure_vocabulary.md` (each `` - `word`： ``
  line) and `data/market_series.json` (the market codes). A doc that yields none of them, or a key
  the program does not write, stops the command and names the doc.
- The record's JSON schema is built from those rules: the targets, the exposure words, the markets,
  the headings and the source ids are enums, so the agent is held to them and the program checks
  them again.
- Passages are compared with runs of white space made one space, as the spec says. The page text
  given to the agent is the same text the passages are looked for in.
- The number rule: 萬, 億, 兆 or 碼 right after an Arabic digit, a full-width digit, or one of
  〇零一二兩三四五六七八九十百千半, in the title or an item; keyword groups are not checked (section 一).
- The language rule: an item citing a source whose `lang` starts with `zh` has a Han character; one
  citing a source in another language has none.
- Cost per run: one agent run to find the events (or one to sort the given pages), one request per
  page and per site's robots.txt, spaced 5 seconds per site; one read of the daily closes for the
  span of the events' dates; two agent runs per event (writing and checking), four when the first
  record fails, each with the chat's time limit. The folder is read only for the files dated on or after the start date (by their
  file names), to list the events it has and to find an event already written.

## Files

- `chat_bridge/collect/rules.py`: the targets, headings, keys, exposure words and markets read from
  the docs and the markets file.
- `chat_bridge/collect/pages.py`: reading pages and feeds into plain text with their title, site and
  date; the collected-page files and the feed-summary fallback are removed.
- `chat_bridge/collect/channels.py`, `channels_prompt.md`: the agent asked for events with their
  source pages; each page checked against its channel's site; the start date from the folder.
- `chat_bridge/collect/grouping.py`, `grouping_prompt.md`: given pages sorted into events.
- `chat_bridge/collect/record.py`, `writing_prompt.md`: the record schema, the writing question, and
  the program's checks.
- `chat_bridge/collect/checking.py`, `checking_prompt.md`: the second reader's question and answer.
- `chat_bridge/collect/truth_files.py`: the folder's files (dates, titles, cited pages), the file
  name, and a record written in the 71 files' layout.
- `chat_bridge/collect/truth.py`: one event from its pages to a file in the folder.
- `chat_bridge/collect/news_files.py`: the `event_time` rule made public, so the record is checked
  with it before a file exists.
- `chat_bridge/collect/cli.py`: the default folder is `data/truth`; `--until`; no ingest; the
  progress lines.
- `tests/collect/`: the rules read from the docs; each check with stand-in records; a two-source
  event to a file, section by section; the second reader's refusal; the command with stand-in
  agent and pages.
- `README.md`, `README_tzh.md`; `docs/truth_format.md` section 7's command line.
