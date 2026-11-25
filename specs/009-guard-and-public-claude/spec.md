# Feature Specification: The guard, shared

**Feature Branch**: `009-guard-and-public-claude` (feature directory; no git branch is tied to it)

**Created**: 2026-11-25

**Status**: Draft

**Input**: User description: "The hook that checks the coding sessions' shell, file and message calls is split by use, its holes are closed, and the parts of `.claude/` that show how the sessions are limited are put in the repository; personal settings, internal notes and the role list stay out."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - See how the coding sessions are limited (Priority: P1)

A person who reads the repository opens `.claude/` and finds the hook that runs before every
shell, file and message call, the settings that load it, the deny rules for secret files, the
Spec Kit skills and the instructions every session loads, with a README that says what the hook
stops and what it does not.

**Acceptance Scenarios**:

1. **Given** a clone, **When** the person lists `.claude/`, **Then** `CLAUDE.md`, `settings.json`, `hooks/` (without `roles.json`) and `skills/` are there, and nothing else from `.claude/`.
2. **Given** `.claude/settings.json`, **When** it is read, **Then** it holds the hook and the deny rules, and no allow rule.
3. **Given** `.claude/hooks/README.md`, **When** it is read, **Then** it lists what the hook stops, what it does not stop, and the layout of its files.
4. **Given** `.claude/CLAUDE.md`, **When** it is read, **Then** it describes the workflow and the guard, and holds no personal words or internal documents; those are in `CLAUDE.local.md`, which git ignores.
5. **Given** `.claude/hooks/tests/`, **When** `uv run --no-sync pytest .claude/hooks/tests` runs, **Then** every case passes.

### User Story 2 - The holes are closed (Priority: P1)

**Acceptance Scenarios**:

1. **Given** the writer, **When** it writes outside the project, its scratch folder and this project's memory, by file tool or by shell, **Then** it is asked about and logged.
2. **Given** any session, **When** a shell command sends data to another machine (curl, wget and PowerShell bodies or uploads, gh commands that create or change something, scp, rsync, sftp, ssh, publishing a package or an image), **Then** it is asked about, except this machine's own services and the vulnerability lookups.
3. **Given** any session, **When** it runs a shell command, **Then** the command's first line is logged.
4. **Given** a clone without `roles.json`, **When** a session makes a call, **Then** it has the writer's rules and is not prompted on every call.
5. **Given** the hook cannot run, **When** a matched tool is called, **Then** the call is blocked.
6. **Given** the 145 earlier scenarios, **When** they run against the new hook, **Then** every answer is as before.

## Requirements *(mandatory)*

- **FR-001**: The hook's entry only reads the call, finds the role and hands the call on; the rules are one module per use.
- **FR-002**: The repository tracks `.claude/CLAUDE.md`, `.claude/settings.json`, `.claude/hooks/` except `roles.json`, and `.claude/skills/`; every other file under `.claude/`, and `CLAUDE.local.md`, stays ignored.
- **FR-003**: The tracked settings hold no allow rule; each person's allow rules live in their own `.claude/settings.local.json`.
- **FR-004**: The tracked files hold no personal name, e-mail, local path or session id.

## Success Criteria *(mandatory)*

- **SC-001**: The earlier scenarios and the hole scenarios all pass; replaying recent real calls gives the same answers as before.
- **SC-002**: `git status --short -uall` after the change shows no `roles.json`, `guard.log`, `docs/`, `CLAUDE.local.md` or `settings.local.json`.
