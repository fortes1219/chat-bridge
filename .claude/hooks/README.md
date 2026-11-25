# Guard

Claude Code runs `guard.py` before every Bash, PowerShell, Edit, Write, NotebookEdit, SendMessage
and Workflow call (`.claude/settings.json`). It answers deny, ask (the person at the keyboard gets a
prompt) or allow, or says nothing and leaves the call to the normal permission flow. If the guard
itself fails to run, the call is blocked (`"onFailure": "block"`, Claude Code 2.1.295 or later), not
let through. The hook runs `python`, so a `python` command must be on the PATH; on a machine with
only `python3`, every Bash and file call is blocked until the command in `.claude/settings.json` is
changed.

## What it stops

| Rule | Answer |
|---|---|
| `git commit`, `git push` | deny, for every session |
| Installing or removing packages; `git add`, `checkout`, `reset`, `stash` and other changes to the repository state | ask |
| Changing the guard, its role list or the settings that load it | ask (writer), deny (reviewer) |
| Editing a repository file while the feature in progress has no spec, plan and tasks, has an open `[NEEDS CLARIFICATION]`, or has no complete Packages table in `research.md` (a need without an installable package, a GPL or AGPL license, a citation without commit and line) | deny, by file tool or by shell |
| Writing outside the project, the session's scratch folder and this project's memory (another project's memory included), by file tool or by shell | ask |
| Deleting a folder outside the scratch folder | ask |
| Sending data to another machine: `curl -d`, `-F`, `-T`, `-X POST` (glued forms such as `-XPOST` included), `wget --post-*`, `Invoke-RestMethod -Body`, `gh` commands that create or change something, `scp`, `rsync` or `sftp` to a remote host, `ssh`; this machine's own services and the OSV vulnerability lookups are not asked about | ask |
| The reviewer changing any project file outside `.claude/docs/`, running the project, a model CLI or an installer, or changing a repository | deny |
| Reading `.env` files and the Claude Code and Codex login files | deny, by the `permissions.deny` rules in `.claude/settings.json` |

Every shell command (its first line and how many lines follow; a heredoc's body is not kept),
every message between sessions, every edit of a repository file or of a file under `.claude/`, and
every refusal and prompt is written to `.claude/guard.log` (kept on this machine).

## What it does not stop

- Shell commands are read, not run. A program that reads or writes files by itself, such as a
  Python script started from the shell, is not seen; neither is a command whose text the guard
  cannot parse, which is only logged.
- Reading files is not checked, except for the paths the deny rules name, and the deny rules
  cover Claude's file tools and the file commands Claude Code recognizes, not scripts.
- Native Windows has no sandbox for Claude Code, so none of this is an operating-system boundary.

## Roles

`roles.json` lists the session ids of the writer and the reviewer:

```json
{ "writer": ["<session id>"], "reviewer": ["<session id>"] }
```

It is private, so a clone has none. Without it every session is the writer: code still waits for
its spec, and commits, installs, writes outside the project and uploads still stop. The cost: if
the file goes missing on a machine that has a reviewer, the reviewer's limits are gone without a
warning. A session that is in neither list gets the reviewer's limits as ask instead of deny.

## Layout

```
hooks
│
├── guard.py                  entry: reads the call, finds who is calling, hands the call on
├── roles.json                session ids of the writer and the reviewer (private)
│
├── validators                the rules, one module per use
│   ├── every_role.py         logging every command; commits, installs, repository changes, uploads
│   ├── self_protection.py    the guard's own files and the settings that load it
│   ├── spec_gate.py          code waits for its spec, plan, tasks and Packages table
│   ├── writer.py             the writer's file and shell rules
│   ├── messages.py           messages between sessions are logged
│   └── reviewer              the reviewer's limits (also for a session in neither list)
│       ├── files.py          file tools: internal documents, scratch folder, memory only
│       ├── shell.py          shell: one simple command at a time
│       ├── commands.py       which commands it may run, and the checks
│       ├── git.py            git that reads; changes only in the scratch folder
│       ├── targets.py        where its shell may write, and what it may run
│       └── refusal.py        deny for the reviewer, ask for an unlisted session
│
└── utils                     what every rule shares
    ├── roles.py              who is calling
    ├── calls.py              the file or command a call names
    ├── decision.py           the answer to Claude Code, and the log
    ├── places.py             the folders the guard knows
    └── shell                 reading a shell command without running it
        ├── words.py          split into simple commands; arguments
        ├── paths.py          variables and cd, to the path a word names
        ├── writes.py         which paths a command writes
        └── reading.py        one simple command: name, words, paths written
```
