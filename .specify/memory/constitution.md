# chat-bridge Constitution

chat-bridge is a public demo: it ingests documents about market events, answers questions about
them in a chat, and lets an agent propose changes to an investment profile that a person accepts
or rejects. It is a local, single-user demo, not a product.

## Core Principles

### I. Ecosystem Precedent First

Every non-trivial approach MUST cite an open-source precedent in the feature's `research.md`
before it is built: repository, commit, file and line. An approach with no precedent MUST NOT be
invented; it is recorded as a `[NEEDS CLARIFICATION]` marker and stops at the maintainer.

Rationale: an approach copied from a project that already works costs a lookup; an invented one
costs the time to find out why nobody does it that way.

### II. Clone and Run

After cloning, one command MUST start the demo: `uv run chat-bridge`. The reader's machine is
assumed to have Python, Node.js and their own logged-in Claude Code, and nothing else. `uv.lock`
is committed. The demo MUST NOT use the author's API key or login: whoever runs it uses their own
unmodified Claude Code.

Rationale: someone evaluating the demo who has to install a database or obtain a key will not
run it.

### III. The Model Sees Only Retrieved Passages

The answering model MUST receive only the passages retrieval returned, with their file name,
event date and heading path. Raw source files go to the embedding model only. Queries and
documents MUST use the same local embedding model, and code MUST refuse a mismatch.

Rationale: this is what makes the answer traceable to its sources, and what retrieval is for.

### IV. Untrusted Content Stays Data

Ingested documents and chat input are data, never instructions. The model MUST run with all
tools off. User text and retrieved passages MUST reach it through standard input, never the
command line. The disclosure text and the source list MUST be attached by code, not written by
the model.

Rationale: no prompt wording reliably stops injection, so the guarantee is structural: whatever
the model is talked into, it can only produce text, and it cannot remove the notice or the sources.

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

## Development Workflow

- Work follows Spec Kit: specify, clarify, plan, tasks, implement, converge. Code for a feature
  is not edited until its `spec.md`, `plan.md` and `tasks.md` exist and neither the spec nor the
  plan carries a `[NEEDS CLARIFICATION]` marker.
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

**Version**: 1.0.0 | **Ratified**: 2026-11-20 | **Last Amended**: 2026-11-20
