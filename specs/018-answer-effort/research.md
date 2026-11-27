# Research: How hard the answering model thinks

Sources were opened on 2026-11-27. A citation `owner/repo@commit:path:line` points at the file as it
was at that commit. Claude Code's documentation is cited by page and line of its Markdown file.

## Packages

| Need | Package | Version | License | Size | Dependency declared in | Called in |
|---|---|---|---|---|---|---|
| A choice of three in the question box's footer (decision 5) | @nuxt/ui | 4.13.0 | MIT | none added: already a dependency | `nuxt-ui-templates/chat-vue@ce4ef47:package.json:22` | `nuxt-ui-templates/chat-vue@ce4ef47:src/components/chat/Prompt.vue:66-70`; `src/components/ModelSelect.vue:8-20` |
| The level in the page's request schema, checked before it is sent | zod | 4.6.7 | MIT | none added: already a dependency | `middleapi/orpc@26175d2:playgrounds/contract-first/package.json:23` | `middleapi/orpc@26175d2:playgrounds/contract-first/src/contract/sse.ts:2`, `:11` |
| The level in the service's request model, refused when it is not one of three | pydantic | 2.14.3 | MIT | none added: already a dependency | `fastapi/full-stack-fastapi-template@77e550a:backend/pyproject.toml:10` | `Azure-Samples/rag-postgres-openai-python@ecaafc4:src/backend/fastapi_app/api_models.py:5`, `:93-97` |

No package is added.

## Advisories

No package or runtime is added or changed. The lock files are sent to OSV and `npm audit` again
before this feature is delivered, as for every delivery.

## Decisions

### 1. The three words and each program's option

- **Decision**: `low`, `medium` and `high`. Claude Code is started with `--effort <level>`, Codex
  with `-c model_reasoning_effort='<level>'`, the single quotes making a TOML string as the
  `web_search` option already is.
- **Rationale**: Claude Code: "`--effort` | Set the effort level for the current session. Options:
  `low`, `medium`, `high`, `xhigh`, `max`, or `ultracode`. Available levels depend on the model."
  (cli-reference.md:89); `claude --help` of the 2.1.328 installed here lists `--effort <level>`
  with low, medium, high, xhigh, max. Codex 0.171.0 (tag `rust-v0.171.0`, commit `ccf9be8`): the
  configuration has `pub model_reasoning_effort: Option<ReasoningEffort>`
  (`openai/codex@ccf9be8:codex-rs/config/src/config_toml.rs:414`), whose values include `low`,
  `medium`, `high` (`codex-rs/protocol/src/openai_models.rs:74-81`, `:162-164`); `codex exec
  --help`: "`-c, --config <key=value>` Override a configuration value … The `value` portion is
  parsed as TOML." The three are the levels both programs name alike; only these are offered.

### 2. Every model run of the question takes the level

- **Decision**: The split, the answer, and the answer with a proposal all run at the chosen level.
- **Rationale**: The wait the person sees is the split and the answer together; questions about
  events and revisions of the strategy were named as the slow ones, and both go through the split
  first.

### 3. What "Default" is

- Without a level each program uses its model's default. Claude Code: "Fable 5.2, Opus 5.5, Sonnet
  5.5, and Haiku 5.5 default to `medium`, and Opus 4.7 defaults to `xhigh`. Other models in the
  effort levels table default to `high`." (model-config.md:669). Codex: the model's
  `default_reasoning_level`; the first model of the list bundled with Codex 0.171.0, `gpt-6.2-sol`,
  has `low`, and offers `low`, `medium`, `high`
  (`openai/codex@ccf9be8:codex-rs/models-manager/models.json:4`, `:43`, `:46`, `:50`, `:54`).
- **Decision**: The same for both programs: Fast `low`, Default `medium`, Precise `high`. For Codex
  on `gpt-6.2-sol`, Fast is what it ran at before this feature and Default is one level above it;
  the maintainer chose this over keeping Codex's own default for Default.

### 4. The shell does not set the level

- **Decision**: `CLAUDE_CODE_EFFORT_LEVEL` is left out of Claude Code's environment, for every run.
- **Rationale**: Claude Code takes "the first that applies" of: "1. The `CLAUDE_CODE_EFFORT_LEVEL`
  environment variable … 3. Launching with `--effort` 4. Your settings" (model-config.md:663-668).
  The settings are already kept out by `--restricted` (`chat_bridge/chat/claude_code.py`,
  `SETUP_ARGS`); the variable is the one part of the person's setup that would still come before
  the page's choice. Codex reads its level from its configuration, and `--ignore-user-config`
  already keeps the person's `config.toml` out; a `-c` value applies on top of it, as
  `web_search` does.
- `collect` and `truth` pass no level; without the variable their runs use the model's default
  rather than the shell's.

### 5. The choice sits in the question box's footer

- **Decision**: A `USelect` of three items in `UChatPrompt`'s footer slot; the send button stays
  where it is.
- **Rationale**: Nuxt UI's own chat template puts its model choice in the prompt's footer
  (`nuxt-ui-templates/chat-vue@ce4ef47:src/components/chat/Prompt.vue:66-70`, a `USelectMenu` in
  `src/components/ModelSelect.vue:8-20`). Three fixed items need no search, so `USelect`, as the
  page's language choice already is (`frontend/src/views/chat/ChatPage.vue`).

### 6. The choice is kept in the address

- **Decision**: `effort` in the address beside `lang` and `program`, read and corrected by the same
  composable: a value that is not one of the three is replaced by `medium`.
- **Rationale**: The page keeps its choices in the address so a reload or a shared link opens the
  same view (`frontend/src/views/chat/composables/useAddressState.ts`).

### 7. A level the model does not have

- Claude Code: "If you set a level the active model does not support, Claude Code falls back to the
  highest supported level at or below the one you set." and "Models not listed here do not support
  effort" (model-config.md:661, :653). All three levels are in the table for every model it lists
  (:657-659).
- Codex: what it does with a level the model does not list was not read in its code.

## Not verified

- Precise (`high`) was not measured. What Codex does with a level its model lacks was not seen:
  the model the run used had both levels.

## Runs

### As a person, with a stand-in program (2026-11-27, 12:36 to 12:37)

`uv run chat-bridge --no-browser` on a copy of the database, with a stand-in `claude` that records
each command line, and `CLAUDE_CODE_EFFORT_LEVEL=max` set where the service started; the page
walked in headless Edge with the mouse, on the Traditional Chinese page:

- The choice is in the question box's footer and shows 預設; the address read
  `?lang=zh-TW&effort=medium&program=claude-code`.
- Opened with the mouse, it listed 快速, 預設, 精準. Choosing 快速 changed the address to
  `effort=low`; after a reload it still showed 快速.
- One question: the split and the answer were both started with `--effort low`, and neither had
  `CLAUDE_CODE_EFFORT_LEVEL` in its environment. The question's record has `"effort": "low"`.
- Ctrl+C ended the service in 6.6 seconds with none of its processes left and the database
  stopped.

An earlier attempt the same minute walked another chat-bridge service already listening on the
port, since the run's own service found the port taken and exited; one question reached that
service's logged-in Claude Code. The walk now stops when the port is in use before it starts.

### The real run (2026-11-27, 13:16 to 13:21, with the maintainer's consent)

`uv run chat-bridge --no-browser` on a copy of the database, with the maintainer's logged-in Claude
Code 2.1.328 and Codex 0.171.0 and live prices; one allocation request, `依照過往2個月的事件，調整我現在的持股策略`
with `用途: 避險` on its second line, sent to `POST /chat/stream` once per program and level, one
after another:

| Program | Level | Context (s) | Answer (s) | Sources | Proposal |
|---|---|---|---|---|---|
| Claude Code | low | 10.2 | 85.6 | 102 | kept |
| Claude Code | medium | 9.3 | 107.6 | 108 | kept |
| Codex | low | 9.5 | 40.4 | 100 | kept |
| Codex | medium | 9.1 | 42.6 | 98 | kept |

- The answer of an allocation request arrives whole, so the first words and the end came within
  0.3 seconds of each other. The split took 7.3 to 7.8 seconds in all four.
- The records show the level on both runs of each question: `--effort low` and `--effort medium`
  for Claude Code, `-c model_reasoning_effort='low'` and `'medium'` for Codex. Codex accepted the
  setting under `--ignore-user-config`.
- The input to the model was 86,924 to 97,989 characters.
- Each figure is one run; the answers' lengths differed (1,307 to 2,546 characters), so the
  seconds are not the level's alone.
- Ctrl+C ended the service in 2.3 seconds with none of its processes left and the database
  stopped.

### Checks

ruff, ruff format, mypy (61 files), the fast suite (745), Prettier, ESLint, vue-tsc, Vitest (163),
the build. `uv.lock` and `package-lock.json` did not change; `npm audit` lists only the five
moderate advisories of the test-only chain kept before (`@vue/test-utils` to `js-beautify`).
