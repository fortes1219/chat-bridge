# Research: The guard, shared

## Packages

No package is added. The hook and the deny rules are Claude Code's own; the hook's code uses the
Python standard library only.

| Need | Package | Version | License | Size | Dependency declared in | Called in |
|---|---|---|---|---|---|---|
| Check each tool call before it runs | Claude Code PreToolUse hook | Claude Code 2.1.295 or later | Anthropic Commercial Terms | none: part of Claude Code | `disler/claude-code-hooks-mastery@052ad1cbd5ae:.claude/settings.json:25` | `disler/claude-code-hooks-mastery@052ad1cbd5ae:.claude/settings.json:31` |
| Refuse reading secret files | Claude Code permission deny rules | Claude Code | Anthropic Commercial Terms | none: part of Claude Code | `supabase/supabase@fcbdda81072c:.claude/settings.json:3` | `supabase/supabase@fcbdda81072c:.claude/settings.json:4` |

## Advisories

None: nothing is installed.

## Decisions

0. **An entry that only wires, with the rules in modules beside it.** Anthropic's hookify plugin
   puts its folder on the import path and imports its rules from `core/`
   (anthropics/claude-plugins-official@5cec67167672 `plugins/hookify/hooks/pretooluse.py:13-19`).
   Where hookify lets the call through when an import fails (`:20-22`), this guard asks.
1. **Shared settings carry the hook and deny rules, not allow rules.** Public repositories commit
   `.claude/settings.json` with hooks and deny rules (supabase@fcbdda81072c `.claude/settings.json:2-35`);
   allow rules are personal and go to `.claude/settings.local.json`, which Claude Code documents as
   the place it saves them (code.claude.com/docs/en/permissions, "Permission system").
2. **Block when the hook fails.** A failed hook lets the call through unless the hook sets
   `"onFailure": "block"` (code.claude.com/docs/en/hooks, "Block the action when a hook fails").
3. **Ignore `.claude/*` and list what is shared.** Git cannot re-include a file whose parent folder
   is excluded, so `.claude/` becomes `.claude/*` followed by `!` lines.
