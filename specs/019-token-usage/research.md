# Research: How many tokens a question used

Sources were opened on 2026-11-27. A citation `owner/repo@commit:path:line` points at the file as it
was at that commit. Claude Code's documentation is cited by page and line of its Markdown file.

## Packages

| Need | Package | Version | License | Size | Dependency declared in | Called in |
|---|---|---|---|---|---|---|
| The usage event in the service's stream model, checked as the other events are | pydantic | 2.14.3 | MIT | none added: already a dependency | `fastapi/full-stack-fastapi-template@77e550a:backend/pyproject.toml:10` | `Azure-Samples/rag-postgres-openai-python@ecaafc4:src/backend/fastapi_app/api_models.py:5`, `:93-97` |
| The usage event in the page's contract, refused when it is not that shape | zod | 4.6.7 | MIT | none added: already a dependency | `middleapi/orpc@26175d2:playgrounds/contract-first/package.json:23` | `middleapi/orpc@26175d2:playgrounds/contract-first/src/contract/sse.ts:2`, `:11` |

No package is added.

## Advisories

No package or runtime is added or changed. The lock files are sent to OSV and `npm audit` again
before this feature is delivered, as for every delivery.

## Decisions

### 1. Claude Code's numbers come from `modelUsage`

- **Decision**: input = `inputTokens` + `cacheReadInputTokens` + `cacheCreationInputTokens`,
  cached input = `cacheReadInputTokens`, output = `outputTokens`, summed over the models of
  `modelUsage` in the run's result.
- **Rationale**: The result of `--output-format json` and the last message of `stream-json` are
  the SDK's result message, which carries `usage` and `modelUsage`; the documentation says `usage`
  is the "main agent loop only … Prefer `modelUsage` for token/cost accounting", and that
  `modelUsage` covers "every model call made through the query pipeline"
  (agent-sdk/typescript.md:1895-1896, :1954-1955). Its fields are `inputTokens`, `outputTokens`,
  `cacheReadInputTokens`, `cacheCreationInputTokens` (:5361-5374), and "`outputTokens` already
  includes" the thinking tokens (:5377). The headless page: the JSON response includes "a
  per-model cost breakdown" (headless.md:136) and "usage" (:174). Claude Code's `Usage` is the
  API's, whose `input_tokens` and the two cache counts are separate fields (:5408-5412), so the
  cache is added to make the input whole.

### 2. Codex's numbers come from `turn.completed`

- **Decision**: input = `input_tokens`, cached input = `cached_input_tokens`, output =
  `output_tokens`.
- **Rationale**: `exec --json` writes a `turn.completed` event with `usage`
  (`openai/codex@ccf9be8:codex-rs/exec/src/exec_events.rs:20-21`, `:50-52`), whose fields are
  `input_tokens`, `cached_input_tokens`, `cache_write_input_tokens`, `output_tokens`,
  `reasoning_output_tokens` (`:61-73`), filled from the thread's running total
  (`event_processor_with_jsonl_output.rs:119-128`, `:536-538`). The input already holds the cache:
  Codex's own "non-cached input" is input minus cached (`codex-rs/protocol/src/protocol.rs:2764-2771`),
  and its test has input 100 with 40 read from the cache and 60 written to it
  (`codex-rs/codex-api/src/sse/responses.rs:941-945`); the output holds the reasoning, filled from
  the API's `output_tokens` (`:133-141`).

### 3. One last event with the question's total

- **Decision**: `response.completed`, with `usage` holding `input_tokens`, `cached_input_tokens`,
  `output_tokens`, `total_tokens` and `unreported_runs`.
- **Rationale**: The stream's event names follow OpenAI's Responses events; its last event is
  `response.completed` (`openai/openai-python@f2b2399:src/openai/types/responses/response_completed_event.py:11-20`)
  with usage fields `input_tokens`, `output_tokens`, `total_tokens`
  (`src/openai/types/responses/response_usage.py:40-59`). A run that reported nothing is counted,
  so a partial total never passes for a whole one.

### 4. Shown under each answer

- **Decision**: One line in the block under the answer, after the cited sources' line and the
  data's latest date, once the answer has been typed out.
- **Rationale**: open-webui shows a reply's usage with the reply
  (`open-webui/open-webui@fef778d:src/lib/components/chat/Messages/ResponseMessage.svelte:1304-1326`;
  its license is cited, not copied).

## Runs

### As a person, with a stand-in program (2026-11-27, 14:13)

`uv run chat-bridge --no-browser` on a copy of the database, with a stand-in `claude` whose results
carry made-up `modelUsage` (the split: 1,200 input, 800 read from the cache, 60 output; the answer:
30,000 input, 60,000 read from the cache, 2,000 written to it, 1,990 output); one question on the
Traditional Chinese page in headless Edge. Under the answer, after the data's latest date and
before the notice: 「這一題用了 96,050 個 token（輸入 94,000、輸出 2,050）」, the two runs added as
FR-001 says. No line said a run was unreported. Ctrl+C ended the service in 6.6 seconds with none
of its processes left and the database stopped.

### The real run (2026-11-27, 14:21 to 14:23, with the maintainer's consent)

`uv run chat-bridge --no-browser` on a copy of the database, with the maintainer's logged-in Claude
Code 2.1.328 and Codex 0.171.0; the question 「聯準會這半年的動向對股市有什麼影響？」 asked once
on the Traditional Chinese page in headless Edge with each program, at Default:

| Program | Split in / out | Answer in / out | The page's line | Seconds |
|---|---|---|---|---|
| Claude Code | 3,380 / 313 | 65,883 / 3,772 | 這一題用了 73,348 個 token（輸入 69,263、輸出 4,085） | 83.7 |
| Codex | 13,098 / 132 | 40,162 / 1,037 | 這一題用了 54,429 個 token（輸入 53,260、輸出 1,169） | 36.5 |

- Both programs reported their counts on both runs: Claude Code's result had `modelUsage`, and
  Codex's `turn.completed` had `usage`. No run was unreported.
- Each line is the sum of the two runs in the question's record.
- Every run reported 0 tokens read from the cache; why was not looked into.
- Ctrl+C ended the service in 6.8 seconds with none of its processes left and the database
  stopped.

### Checks

ruff, ruff format, mypy (61 files), the fast suite (765), Prettier, ESLint, vue-tsc, Vitest (167),
the build.
