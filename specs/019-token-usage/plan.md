# Implementation Plan: How many tokens a question used

**Spec**: [spec.md](spec.md)

## Summary

Each program reads the usage its run reports and hands it to an `on_usage` callback, beside the
`on_start` one it already has. The service adds up the question's runs and ends the stream with a
`response.completed` event carrying the total; the page shows it under the answer.

## Technical Context

- Python 3.11 or later, FastAPI, pydantic; Vue 3 with Nuxt UI, zod, oRPC and TanStack Query.
- No package is added.
- Cost: nothing more is asked of the programs; their own last message is read for numbers already
  in it.

## Files

- `chat_bridge/chat/programs.py`: `Usage`, and `on_usage` on `reply_in_shape` and `stream_answer`.
- `chat_bridge/chat/claude_code.py`, `codex.py`: the usage from the result's `modelUsage`, and
  from the `turn.completed` event.
- `chat_bridge/chat/split.py`, `chat_bridge/strategy/revision.py`, `chat_bridge/chat/service.py`,
  `schemas.py`: each run's usage to the question's total, the last event, the record.
- `frontend/src/service/schema/chat.ts`; `views/chat/composables/useAsk.ts`,
  `components/AnswerContent.vue`; the texts in both languages.
- Tests beside the existing chat tests and page tests.
- `README.md`, `README_tzh.md`.
