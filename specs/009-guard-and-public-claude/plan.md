# Implementation Plan: The guard, shared

**Spec**: [spec.md](spec.md)

## Summary

Split the hook by use (entry, `validators/`, `utils/`), close the holes listed in the spec, move
the allow rules to the personal settings file, add deny rules and block-on-failure to the shared
one, and change `.gitignore` so the shared parts of `.claude/` are tracked.

## Technical Context

- Python 3.11 or later, standard library only; Claude Code 2.1.295 or later for `onFailure`.
- Checked by the earlier 145 scenarios, the hole scenarios, and a replay of recent real calls
  through the old and the new hook.

## Files

- `.claude/hooks/guard.py`, `.claude/hooks/validators/`, `.claude/hooks/utils/`, `.claude/hooks/README.md`
- `.claude/settings.json` (shared), `.claude/settings.local.json` (personal, ignored)
- `.gitignore`
