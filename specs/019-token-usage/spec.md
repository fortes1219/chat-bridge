# Feature Specification: How many tokens a question used

**Feature Branch**: `019-token-usage` (feature directory; no git branch is tied to it)

**Created**: 2026-11-27

**Status**: Draft

**Input**: User description: "Show the total number of tokens on the screen."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See the tokens under each answer (Priority: P1)

Once an answer has ended, a line under it says how many tokens the question used: the total, the
input and the output, added up over every model run of the question.

**Acceptance Scenarios**:

1. **Given** a question answered by Claude Code, **When** the answer ends, **Then** a line reads 「這一題用了 {total} 個 token（輸入 {input}、輸出 {output}）」 on the Traditional Chinese page and "This question used {total} tokens ({input} in, {output} out)" on the English page, with the numbers grouped by thousands.
2. **Given** the same with Codex, **When** the answer ends, **Then** the same line, from Codex's own report.
3. **Given** a question that was split and then answered, or answered with a proposal, **When** the line is shown, **Then** its numbers are the split's run and the answer's run added together.
4. **Given** a run that reported no usage (a split that ran out of time, a run that ended without its last message), **When** the line is shown, **Then** a second line says how many runs reported none and that the numbers leave them out.
5. **Given** an answer the user stopped, or one that failed, **When** it ends, **Then** no such line is shown.
6. **Given** a question the data has nothing on, answered without a model, **When** it ends, **Then** no such line is shown.
7. **Given** the line is shown, **Then** it is in the block under the answer with the cited sources' line and the data's latest date, after them, and covers nothing of the answer.

### User Story 2 - The usage is kept (Priority: P2)

1. **Given** any question a program was run for, **When** its record is read, **Then** it holds each run's usage, or that the run reported none, and the total.

## Requirements *(mandatory)*

- **FR-001**: Claude Code's run, from the `modelUsage` of its result, summed over the models it lists:
  input = `inputTokens` + `cacheReadInputTokens` + `cacheCreationInputTokens`; cached input = `cacheReadInputTokens`; output = `outputTokens`.
  Claude Code's `inputTokens` leaves the cache out, so the cache is added.
- **FR-002**: Codex's run, from the `usage` of its `turn.completed` event:
  input = `input_tokens`; cached input = `cached_input_tokens`; output = `output_tokens`.
  Codex's `input_tokens` already holds the cache read and written, and `output_tokens` the reasoning, so nothing is added.
- **FR-003**: A run's usage that is missing or not whole numbers of zero or more counts as unreported, never as zero.
- **FR-004**: The service adds up every run of the question and, after the answer's last piece, or the proposal of a revision question, sends one last event `response.completed` with `usage`: `input_tokens`, `cached_input_tokens`, `output_tokens`, `total_tokens` = input + output, and `unreported_runs`.
- **FR-005**: The record of the question keeps each run's usage and the total, however the answer ends.
- **FR-006**: The page shows the line of User Story 1 once the answer has ended and been typed out, in the page's language; a stopped, failed or model-less answer has none.
- **FR-007**: The README in both languages says what the numbers count and where they come from.

## Not done

- No cost in money: Claude Code's `total_cost_usd` is an estimate, and a subscription login is not
  billed per token.
- No running count while the answer is written; the numbers come with the answer's end.
- A stopped or failed answer's tokens are not shown on the page; the record keeps what was reported.

## Success Criteria *(mandatory)*

- **SC-001**: Each scenario and requirement has a fast test, on the service or on the page; one test puts the same numbers through both programs' readings to show that the cache is added for Claude Code and not for Codex.
- **SC-002**: Real run, with consent: one question with each logged-in program; the fields are present in what the installed versions write, and the numbers on the page match the sum of the runs in the record.
