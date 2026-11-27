# Feature Specification: How hard the answering model thinks

**Feature Branch**: `018-answer-effort` (feature directory; no git branch is tied to it)

**Created**: 2026-11-27

**Status**: Draft

**Input**: User description: "Beside the question box the person picks how hard the answering model thinks: Fast, Default or Precise, for low, medium and high. Higher levels are not offered, though both programs can go higher. Both Claude Code and Codex take it. Questions about events and revisions of the strategy are slow, and a person will not want to wait that long."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Pick a level beside the question box (Priority: P1)

Before sending a question, the person picks Fast, Default or Precise beside the question box. The
question is answered at that level by the program that answers.

**Acceptance Scenarios**:

1. **Given** the chat is open, **When** the person looks at the question box, **Then** a choice beside it offers Fast, Default and Precise (快速、預設、精準 on the Traditional Chinese page), and Default is chosen.
2. **Given** Fast is chosen, **When** a question is sent, **Then** the request carries `effort: low`, and every model run the question makes (listing its parts for the search, then the answer, or the answer with a proposal) starts at low: Claude Code with `--effort low`, Codex with `-c model_reasoning_effort='low'`.
3. **Given** Default or Precise is chosen, **When** a question is sent, **Then** the same holds with `medium` or `high`.
4. **Given** a level is chosen, **When** the page is reloaded or its address is opened elsewhere, **Then** the same level is chosen: the address keeps it as `effort`, beside `lang` and `program`.
5. **Given** an address whose `effort` is anything else (`xhigh`, `max`, a typo), **When** the page opens, **Then** Default is chosen and the address is corrected.
6. **Given** a request whose `effort` is not one of the three, **When** it reaches the service, **Then** it is refused before any search or program runs; **given** a request without `effort`, **then** it is answered at `medium`.

### User Story 2 - The shell the service runs from does not change the level (Priority: P2)

**Acceptance Scenarios**:

1. **Given** `CLAUDE_CODE_EFFORT_LEVEL` is set where the service was started, **When** Claude Code answers, **Then** it runs at the level the page chose: the variable is left out of its environment, because Claude Code takes it before `--effort`.

## Requirements *(mandatory)*

- **FR-001**: The request's `effort` takes only `low`, `medium` and `high`; without it, `medium`.
- **FR-002**: The level applies to every model run of the question: the split, the answer, and the answer with a proposal.
- **FR-003**: Claude Code is started with `--effort <level>` and Codex with `-c model_reasoning_effort='<level>'`; nothing else on their command lines changes.
- **FR-004**: `CLAUDE_CODE_EFFORT_LEVEL` is left out of Claude Code's environment, as the key variables are.
- **FR-005**: The question's record keeps the level; the command lines it keeps show it.
- **FR-006**: The page offers exactly the three choices, labelled in both languages, beside the question box, and keeps the choice in the address.
- **FR-007**: The README in both languages says what the choice is, what each choice starts each program at, what happens with a model that has no such level, and the seconds measured in the real run.

## What "Default" is for each program

- Without a level, as before this feature, each program uses its model's own default. Claude Code:
  `medium` for Fable 5.2, Opus 5.5, Sonnet 5.5 and Haiku 5.5, `xhigh` for Opus 4.7, `high` for the
  other models with effort levels. Codex: the default of the model it runs; the first model of the
  list bundled with Codex 0.171.0, `gpt-6.2-sol`, defaults to `low`.
- With this feature the two programs are the same: Fast is `low`, Default is `medium`, Precise is
  `high`. For Claude Code on a 5.5 model, Default is what it ran at before. For Codex on
  `gpt-6.2-sol`, Fast is what it ran at before, and Default is one level above it.

## Not done

- `xhigh`, `max` and `ultracode` are not offered.
- `collect` and `truth` take no level: the choice is beside the chat's question box. Their runs use
  each program's own default, as before.
- A level the model does not have: Claude Code runs the highest level the model has at or below
  it, and a model missing from its table of levels does not support effort (its documentation;
  what such a run does with `--effort` is not written there). What Codex does was not read in its
  code. The real run shows both for the models the person's programs use.

## Success Criteria *(mandatory)*

- **SC-001**: Each scenario has a fast test, on the service or on the page.
- **SC-002**: Real run, with consent: one question sent at Fast and at Default to each logged-in program; the seconds to the first words and to the end of each, written in research.md and the README.

## Assumptions

- The person's Claude Code and Codex are recent enough to take the level: Claude Code 2.1.328 and
  Codex 0.171.0 were read here.
