# Implementation Plan: Collect from the channels with the person's own agent

**Spec**: [spec.md](spec.md)

## Summary

`uv run chat-bridge collect` with no address and no path reads `data/channels.json`, takes the
knowledge base's latest event date, and runs the person's own logged-in program once (chosen as the
chat chooses it) with web search and web reading only, asking for the pages the enabled channels
published on or after that date, in a JSON schema. Each page on a channel's site goes to `collect`'s
page collecting (feature 013); the rest are refused and named. The folder is then ingested.

## Technical Context

- Python; no new package. The programs are started as the chat starts them (`chat_bridge/chat/claude_code.py`,
  `codex.py`), with the tool arguments of this feature instead of none.
- Claude Code: `--tools "WebSearch,WebFetch"`, `--allowedTools` with `WebSearch` and
  `WebFetch(domain:<site>)`, `WebFetch(domain:*.<site>)` per channel site, `--json-schema`, and the
  isolation it is already started with otherwise (no user settings, no MCP servers, no session
  saved).
- Codex: `-c web_search="live"` instead of `"disabled"`, the tools that run commands or touch files
  still off, a read-only sandbox in an empty folder, `--output-schema`.
- The limit is the answer time limit the chat already uses for a program run.
- Cost: one agent run per command, then one request per page and per robots.txt, spaced per site;
  one ingest of the folder.

## Files

- `data/channels.json`: the sample's channels.
- `chat_bridge/collect/channels.py`: the channel list, read and checked; the agent's question, its
  answer read and checked against the channel sites.
- `chat_bridge/collect/channels_prompt.md`: what the agent is asked.
- `chat_bridge/chat/claude_code.py`, `codex.py`: a shaped reply with given web tools.
- `chat_bridge/collect/cli.py`: no address and no path collects from the channels; web collecting
  ends with an ingest of the folder.
- `tests/collect/`: the list, the arguments each program is started with, a stand-in agent's
  answer, the refusals, the ingest after collecting.
- `README.md`, `README_tzh.md`.
