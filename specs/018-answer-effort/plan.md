# Implementation Plan: How hard the answering model thinks

**Spec**: [spec.md](spec.md)

## Summary

The chat request gains `effort` (`low`, `medium`, `high`; `medium` without it). The service passes
it to every model run of the question, and each program turns it into its own option: Claude Code's
`--effort`, Codex's `model_reasoning_effort`. The page shows a choice of three in the question box's
footer and keeps it in the address.

## Technical Context

- Python 3.11 or later, FastAPI, pydantic; Vue 3 with Nuxt UI, zod, oRPC and TanStack Query.
- No package is added.
- Cost: nothing new per question; the level is two more words on each command line.

## Files

- `chat_bridge/chat/programs.py`: `Effort`, and the level on `reply_in_shape` and `stream_answer`.
- `chat_bridge/chat/claude_code.py`, `codex.py`: the level on the command lines;
  `CLAUDE_CODE_EFFORT_LEVEL` left out of Claude Code's environment.
- `chat_bridge/chat/schemas.py`, `router.py`, `service.py`, `split.py`,
  `chat_bridge/strategy/revision.py`: the request's level to every run of the question, and into
  the record.
- `frontend/src/service/schema/chat.ts`; `views/chat/constants.ts`,
  `composables/useAddressState.ts`, `composables/useAsk.ts`, `components/ChatPanel.vue`,
  `components/EffortPicker.vue`, `ChatPage.vue`; the texts in both languages.
- Tests beside the existing chat tests and page tests.
- `README.md`, `README_tzh.md`.
