# Research: Codex can answer too

Codex answers through the person's own installed and logged-in Codex CLI. Our code builds the
command line, sends the input and reads the result; it adds no model logic of its own.

## Packages

| Need | Package | Version | License | Size | Dependency declared in | Called in |
|---|---|---|---|---|---|---|
| Answer with the person's own Codex, and report whether it is logged in | Codex CLI (`@openai/codex`, installed by the person) | 0.166.0 or later | Apache-2.0 | none added: the person's own install | `openai/codex@a0436d6:sdk/typescript/src/exec.ts:50` | `openai/codex@a0436d6:sdk/typescript/src/exec.ts:95`, `:215-216` |

Notes on the citations:

- OpenAI's own TypeScript SDK finds the installed `codex` (`exec.ts:50`, `:356`), starts it as
  `codex exec --experimental-json` (`:95`) and writes the input to standard input (`:215-216`).
- `codex login status` is how the CLI reports its own login: exit 0 when logged in
  (`codex-rs/cli/src/login.rs:488-554` at `rust-v0.166.0`, commit `6ff1e1c`).

## Decisions

### 1. Codex runs as the person's own CLI

- **Decision**: the service starts the `codex` program found on the person's machine, as it
  already starts Claude Code.
- **Rationale**: the maintainer asked for the person's own logged-in Codex. It keeps their login
  and their plan, and adds nothing to the clone.

### 2. What Codex may reach and do

- **Decision**: the same as Claude Code, as constitution IV lists them (spec FR-004). In this
  feature it reads the question and the passages and writes the answer. A revised strategy comes
  back in a given format with `--output-schema`
  (`openai/codex@a0436d6:sdk/typescript/src/exec.ts:143`). Further searches go through the
  service's own search, the way a search is a tool the model calls and the service runs
  (`Azure-Samples/rag-postgres-openai-python@ecaafc4:src/backend/fastapi_app/query_rewriter.py:6-49`).
- **Rationale**: each permission follows from what the person must see: an answer from the data,
  a revised strategy shown as a diff, and a machine that hostile text cannot reach.
- **To settle with T002**: the flags that keep Codex from running commands, touching files or
  going online, each cited from Codex's own source at the installed version.

### 3. The answer arrives whole

- **Decision**: Codex's answer is sent to the chat in one piece when it is complete.
- **Rationale**: with `--json`, Codex reports the agent's message only when the item completes
  (`codex-rs/exec/src/event_processor_with_jsonl_output.rs:343-362` at `rust-v0.166.0`).

### 4. Login state

- **Decision**: `codex login status` is run with the same environment as an answer. Exit 0 is
  logged in. Exit 1 is not logged in only when Codex prints `Not logged in`
  (`codex-rs/cli/src/login.rs:545-547`); it also exits 1 when the check itself fails
  (`:498-499`, `:517-518`, `:549-551`), and that, any other ending, or no program is unknown.
  Claude Code's state is read as feature 001 reads it. The response gives only the state, never
  the program's own text, which can include an account address.
- **Rationale**: the program reports on itself; credential files are never opened.

## Real runs (each needs the maintainer's consent)

1. The Fed question in Traditional Chinese (SC-001).
2. The same question in English (SC-001).
3. The world-cup injection in the chat message (US3-2).
4. The hostile test document of feature 001 (US3-3).
5. A test document asking for the contents of a file on the machine (US3-4).

`codex --version` and `codex login status` are also run; they do not call a model.
