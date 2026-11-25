"""The rules the guard applies, one module per use.

Two roles work in this folder (utils.roles):

- The writer writes the code. The project follows Spec Kit, so code can only be edited once the
  feature in progress has a spec, a plan, a task list and a complete Packages table (spec_gate).
  The Owner is prompted only for installs, repository state changes and changes to the guard
  (writer, every_role, self_protection).
- The reviewer may only look up the ecosystem, update the internal documents in .claude/docs/,
  take stock of progress, run shell commands that read, and run the project's checks. It may not
  change any project file, and may not otherwise use what the project has built or a model CLI
  (reviewer). A session listed as neither gets the reviewer's limits as "ask" instead of "deny",
  so the Owner sees what it tried and decides.

Every role: only the Owner commits and pushes (every_role); messages between sessions are logged
(messages).
"""
