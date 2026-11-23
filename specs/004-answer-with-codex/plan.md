# Implementation Plan: Codex can answer too

**Branch**: `dev/rc-0.1.0` (feature directory `specs/004-answer-with-codex/`) | **Date**: 2026-11-21 | **Spec**: [spec.md](spec.md)

## Summary

The chat service answers with either of the two programs a person may have logged in on their
own machine: Claude Code, as today, or Codex. Both sit behind one small interface: report the
login state, and turn a question with its passages into an answer.

- **Codex** is the person's own `codex` CLI, started for each answer with the input on standard
  input and its key variables removed, with the same permissions as Claude Code (spec FR-004):
  no commands, files or going online on the machine; able to hand back a revised strategy. Its
  answer arrives whole.
- **Choosing**: a request may name the program. With no name, Claude Code answers when it is
  logged in, else Codex. A named program that is not logged in is refused, never swapped.
- **Login states**: `GET /chat/programs` gives each program's state without starting a model.
- **Records** name the program that answered, with its command line.

Claude Code is started exactly as before.

## Technical Context

**Language/Version**: Python 3.13 (`requires-python = ">=3.11"`)

**Primary Dependencies**: none added. Codex is the user's own install (0.166.0 here), as Claude
Code is.

**Storage**: No schema change. The record's `details` gains `program`.

**Testing**: pytest. Fast tests build the Codex command line, read its events and login exit
codes, and choose the program, without starting either program. Real runs (research.md) start
the user's Codex with the maintainer's consent.

**Target Platform**: Windows, macOS, Linux. On Windows, npm installs Codex as a `.cmd` launcher;
the command line holds only fixed flags and a folder path, so it passes through it unchanged.

**Project Type**: A command-line tool that also starts a local web service.

**Constraints**: the command line holds no text from the user or the documents; credential files
are never opened; Claude Code's command line does not change (SC-006).

## Constitution Check

| Principle | How this plan meets it |
|---|---|
| I. Ecosystem Precedent First | The person's own Codex CLI (`## Packages` in research.md); every flag is cited from Codex 0.166.0's source or its own help. |
| II. Clone and Run | Nothing to install: a person uses whichever program they already have. |
| III. Raw Documents Go to the Embedding Model | Codex gets what Claude Code gets: the rules, the retrieved passages and the question, never the raw files. |
| IV. Untrusted Content Stays Data | Question and passages on standard input; the notice and sources attached by the service; Codex has the same permissions as Claude Code: no commands, files or going online on the machine, and it can hand back a revised strategy. |
| V. Feature-Based Structure and Clean Code | `chat_bridge/chat/codex.py` beside `claude_code.py`; shared types in `programs.py`; the service picks the module from a table. |
| VI. Cost Follows the Work | One login check per question in the usual case; the second program is checked only when the first is not logged in. |
| VII. Tests Prove What the User Gets | Fast tests for the command line, events, login and choice; real runs for answers and attacks. |
| VIII. Honest Claims | The README states what each program runs with and what the attacks showed. |

Result: passes.

## Project Structure

```text
chat_bridge/chat/
├── programs.py      # Program, Login, LoginStatus, ProgramError: shared by both programs
├── claude_code.py   # unchanged behaviour; its error now derives from ProgramError
├── codex.py         # new: the person's Codex, input on standard input, whole answer
├── service.py       # picks the program, records it
├── schemas.py       # request names an optional program; login states
└── router.py        # GET /chat/programs; POST /chat/stream takes the program

tests/chat/test_codex.py     # command line, events, login exit codes, key variables
tests/chat/test_programs.py  # choosing the program and refusing one that is not logged in
README.md, README_tzh.md     # Codex, the choice, and what each program runs with
```

## Complexity Tracking

None.
