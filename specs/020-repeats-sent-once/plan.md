# Implementation Plan: Repeated tables and notes sent once

**Spec**: [spec.md](spec.md)

## Summary

`model_input` keeps, for the input it is building, the first section number that sent each table
block and each quoted line. A later section's block or line that is already there is written as a
pointer to that number. The two prompts say what a pointer means. The page's sources and the
record are built from the found sections, as before.

## Technical Context

- Python 3.11 or later.
- No package is added.
- Cost: one pass over the lines of the sections already found; no search and no model run is
  added.

## Files

- `chat_bridge/chat/service.py`: `model_input` and a helper that folds a section's text.
- `chat_bridge/chat/answer_prompt.md`, `chat_bridge/strategy/revision_prompt.md`: the sentence on
  the pointer lines.
- `tests/chat/`: a test file for the folding; the input of the existing tests is unchanged when no
  table repeats.
- `README.md`, `README_tzh.md`.
