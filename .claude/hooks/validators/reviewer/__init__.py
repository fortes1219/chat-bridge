"""The reviewer's limits, which a session in neither role list also gets.

The reviewer may only look up the ecosystem, update the internal documents in .claude/docs/, take
stock of progress, run shell commands that read, and run the project's checks: the fast tests, ruff
and mypy through `uv run --no-sync`, `uv lock --check`, and the slow tests by the documented
container command. It may not change any project file, and may not otherwise use what the project
has built (its code, environment, containers, database) or a model CLI.

files covers the file tools, shell the shell; commands, git and targets are the shell's parts.
refusal says no: deny for the reviewer, ask for a session in neither list.
"""

from validators.reviewer.files import check_file
from validators.reviewer.refusal import refuse_workflow
from validators.reviewer.shell import check_shell

__all__ = ["check_file", "check_shell", "refuse_workflow"]
