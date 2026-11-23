# chat-bridge Constitution

chat-bridge is a public demo: it ingests documents about market events, answers questions about
them in a chat, and lets an agent propose changes to an investment profile that a person accepts
or rejects. It is a local, single-user demo, not a product.

## Core Principles

### I. Ecosystem Precedent First

Every need a feature adds MUST be met by an installable package that other open-source projects
already depend on. Our code calls the package and connects it to the rest; it does not rewrite
another project's internals, and following someone else's code line by line does not count as a
precedent.

Before any code is written, the feature's `research.md` MUST have a `## Packages` table with one
row per need and these columns:

| Need | Package | Version | License | Size | Dependency declared in | Called in |
|---|---|---|---|---|---|---|

The last two columns cite a project that depends on the package and calls it, as
`owner/repo@commit:path:line`. GPL and AGPL packages are not used. When no package meets a need,
or the lookup is not done, the row says `none` and the work stops: the gap is reported to the
maintainer, not written by hand. The repository's guard hook refuses code edits while the table
is missing, incomplete, cites no commit and line, names a GPL or AGPL license, or has a `none`
row.

Every package version and every runtime version (Python, Node.js) MUST be free of known security
advisories whose fix it has not reached. Before a version is chosen it is checked against the
OSV database, which gathers the GitHub, PyPI and npm advisories, and the result is recorded in the
feature's `research.md` under `## Advisories` with the date. A runtime is held to a release line
that still gets security fixes, at that line's latest security release. The locks are checked
again before each delivery: `npm audit` for the page, an OSV check of `uv.lock` for the service.
A version with an unfixed advisory is not used; when no fixed version exists, the work stops and
the gap is reported to the maintainer.

Rationale: a package that others depend on has been tested by their users. A hand-written copy
of another project's internals has not, and it carries that project's license. A version with a
known flaw has been tested too, and found wanting.

### II. Clone and Run

After cloning, one command MUST start the demo: `uv run chat-bridge`. The reader's machine is
assumed to have Python, Node.js and their own logged-in Claude Code or Codex, and nothing else.
`uv.lock` is committed. The demo MUST NOT use the author's API key or login: whoever runs it uses
their own unmodified Claude Code or Codex.

Rationale: someone evaluating the demo who has to install a database or obtain a key will not
run it.

### III. Raw Documents Go to the Embedding Model

Raw source files go to the embedding model only. The answering model is given what retrieval
returned, each passage with its file name, event date and heading path, never the raw files.
Queries and documents MUST use the same local embedding model, and code MUST refuse a mismatch.

Rationale: this is what makes the answer traceable to its sources, and what retrieval is for.

### IV. Untrusted Content Stays Data

Ingested documents and chat input are data, never instructions. User text and retrieved
passages MUST reach the answering program through standard input, never the command line. The
disclosure text and the source list MUST be attached by code, not written by the model.

Both answering programs, Claude Code and Codex, have the same permissions, taken from what the
user must see. Each comes with the feature that needs it.

- They read: the user's question; the retrieved passages, never the raw files; the user's
  investment profile; the indicators the user set; market numbers the service hands them as data.
- They may: decide what to search for next, through the service's own search, which returns
  retrieved passages again; write the answer; hand back a revised strategy in a given format,
  which the page shows as a diff.
- They may not: run commands, read or write files, or go online on the user's machine; change the
  user's profile, because what they hand back is a preview the user accepts or rejects.
- The service fetches market data, and code computes the numbers in a diff; the model does
  neither.

The README states what each program runs with and what the recorded attacks showed.

Rationale: no prompt wording reliably stops injection, so the notice and the sources do not
depend on the model, and nothing a user or a document writes can become a command or reach the
machine. The model gets what the user's questions need, not less and not more.

### V. Feature-Based Structure and Clean Code

Code is organised one package per feature, not by technical layer. Repeated things MUST be data
tables with one loop. Lookup tables replace branch chains. Functions return early. Tree walks
iterate; they do not recurse. Types are derived from a single source. An unknown key or value
MUST be refused, never silently defaulted. Comments say why, not what.

Rationale: having read one module, a reader should be able to read every module.

### VI. Cost Follows the Work

The cost of an operation MUST be proportional to that operation's work, not to the size of the
history. Every query has an index, lists are paged, and nothing scans all stored data.

### VII. Tests Prove What the User Gets

A change in behaviour MUST ship with its tests. Fast tests run on the host with `uv run pytest`.
Tests that need the embedding model and the database are marked `slow` and run in the Linux
container with `docker compose -f compose.test.yml run --rm slow-tests`. A feature that only
works if the model actually uses something MUST ship with the record of a real run.

### VIII. Honest Claims

Retrieval raises accuracy; it does not make answers complete or always right, and the project
MUST NOT claim otherwise. Answers state the date their data reaches, say so when the data holds
no answer, and carry a fixed notice that they are not investment advice. Measured numbers are
reported as measured, together with what they measure.

## Repository Hygiene

- Tracked content is written in English, with LF line endings.
- Commit messages are one line with a conventional prefix. Commits are made by the maintainer.
- Tracked files, images and containers MUST NOT contain secrets, credentials, personal data or
  machine-specific details. A container mounts only the files it needs, read-only.

## Frontend Standards

The page is built to the maintainer's engineering standard. A plan that departs from any of these
is changed, not justified.

- **Contract first, with zod and oRPC.** The data layer has four parts: zod schemas, each strict;
  an oRPC contract that declares each call once and from which the types are inferred, never
  written a second time; API functions that check every response, and every streamed event,
  against its schema where it enters the page; and one request module that does the transport.
  A response that does not match is an error, never data.
- **Server state through TanStack Query.** Loading, error, caching and cancellation come from it;
  no component keeps its own copy of request state.
- **Real-time data over Socket.IO.** Live market quotes arrive on a Socket.IO connection. Chat
  answers do not: they stream in the response to the POST that asked.
- **At most three levels.** Components nest at most three levels deep, composables at most three,
  routes at most three, and i18n message keys at most three.
- **Feature folders.** A feature keeps its pages, components and composables together. Only
  mechanisms with no business content are shared.
- **Vue as written here.** `<script setup lang="ts">` only; `computed` before `watch`; no `any`;
  repeated things are data with one loop in the template; every request can be cancelled; what must
  survive a reload (language, filters, the open tab) lives in the address.
- **One component set.** Nuxt UI with its chat components, on Tailwind. No second component set.
  Markdown from the model or a document is rendered with sanitising on.
- **Both languages.** Every text of the page exists in Traditional Chinese and English.

## Development Workflow

- Work follows Spec Kit: specify, clarify, plan, tasks, implement, converge. Code for a feature
  is not edited until its `spec.md`, `plan.md` and `tasks.md` exist, neither the spec nor the
  plan carries a `[NEEDS CLARIFICATION]` marker, and its `research.md` has the complete
  `## Packages` table of Principle I.
- The maintainer approves a feature once, at its spec and plan. After that the work runs to the
  end of the task list. Conflicts and ambiguities met on the way are decided, recorded with the
  reason, and reviewed afterwards; they do not stop the work.
- Work stops for the maintainer only for: an irreversible or destructive operation, a
  security-sensitive action, a side effect outside the repository, an approach with no precedent,
  or a change to what the spec requires.
- Code is written by one party and checked by another. The check compares each acceptance
  scenario and success criterion against evidence: a file and line, or actual output.

## Governance

This constitution outranks plans and task lists. A plan that departs from a principle either
changes, or records the departure and its justification under Complexity Tracking. Amendments
are made by the maintainer and versioned semantically: a removed or redefined principle is a
major change, a new principle or section a minor one, a clarification a patch. Every plan's
Constitution Check and every review verifies compliance.

**Version**: 3.1.0 | **Ratified**: 2026-11-20 | **Last Amended**: 2026-11-22
