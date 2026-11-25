# chat-bridge: instructions for the coding sessions

Claude Code loads this file in every session. Personal instructions live in `CLAUDE.local.md` at the
repository root, which git ignores.

Two Claude Code sessions build this repository: a writer that writes the specs, the code and the
tests, and a reviewer that checks them. The maintainer commits and pushes; no session does.

## Workflow: Spec Kit

Every piece of work is a feature under `specs/NNN-name/`: `spec.md`, `plan.md`, `research.md`,
`tasks.md`. The rules every feature follows are in `.specify/memory/constitution.md`; the steps are
the `/speckit-*` skills in `.claude/skills/`.

- Code waits for its spec, plan and tasks, and for a Packages table in `research.md` that names an
  installable package for each need, with where another project declares and calls it.
- No GPL or AGPL code; no rewriting another project's code by hand.
- Before choosing a version, look up its advisories and use a fixed one.

## The guard

`.claude/settings.json` runs `.claude/hooks/guard.py` before every shell, file and message call,
and denies reading `.env` files and the login files of Claude Code and Codex. What the guard stops,
what it does not, and how to run its tests are in `.claude/hooks/README.md`. Do not work around it;
changing it needs the maintainer's approval.

## What goes into the repository

English, with LF line endings. No personal names, e-mail addresses, local paths or session ids.
