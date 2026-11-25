"""The reviewer's git: anything that reads or lists; a clone or a change only in its scratch folder,
never in the project repository."""

from __future__ import annotations

from utils.places import PROJECT_DIR, is_inside, is_scratch
from utils.roles import Caller
from utils.shell.paths import ShellState, shell_path
from utils.shell.words import without_values

from validators.reviewer.refusal import refuse
from validators.reviewer.targets import check_targets

# git subcommands that change no repository.
GIT_READS = {
    "status",
    "log",
    "diff",
    "show",
    "ls-files",
    "ls-tree",
    "ls-remote",
    "rev-parse",
    "blame",
    "annotate",
    "cat-file",
    "grep",
    "describe",
    "shortlog",
    "help",
    "version",
    "count-objects",
    "for-each-ref",
    "show-ref",
    "show-branch",
    "name-rev",
    "merge-base",
    "rev-list",
    "whatchanged",
    "check-ignore",
    "check-attr",
    "var",
    "diff-tree",
    "diff-index",
    "diff-files",
    "range-diff",
}
GIT_VALUE_OPTIONS = {
    "-C",
    "-c",
    "--git-dir",
    "--work-tree",
    "--namespace",
    "--exec-path",
}
GIT_CLONE_VALUE_OPTIONS = {
    "--depth",
    "-b",
    "--branch",
    "-o",
    "--origin",
    "--reference",
    "-c",
    "--config",
    "-j",
    "--jobs",
    "--template",
    "--separate-git-dir",
    "-u",
    "--upload-pack",
    "--shallow-since",
    "--shallow-exclude",
    "--filter",
}
# Subcommands that only list when every argument is one of these. Bare `git stash` stashes.
GIT_LISTS = {
    "branch": {
        "-a",
        "-r",
        "-v",
        "-vv",
        "--list",
        "--all",
        "--remotes",
        "--show-current",
    },
    "remote": {"-v", "--verbose"},
    "stash": {"list"},
    "worktree": {"list"},
    "tag": {"-l", "--list"},
}
GIT_LISTS_WHEN_BARE = {"branch", "remote", "tag"}
GIT_CONFIG_READS = {"--get", "--get-all", "--list", "-l", "--get-regexp"}


def check_git(
    caller: Caller, tool_name: str, arguments: list[str], state: ShellState
) -> None:
    repository = state.base
    index = 0
    while index < len(arguments) and arguments[index].startswith("-"):
        option = arguments[index]
        if option == "-C" and index + 1 < len(arguments):
            repository = shell_path(
                arguments[index + 1], ShellState(repository, state.variables)
            )
        index += 2 if option in GIT_VALUE_OPTIONS else 1
    if index >= len(arguments):
        return
    subcommand, rest = arguments[index], arguments[index + 1 :]
    if subcommand in GIT_READS:
        return
    if (
        subcommand in GIT_LISTS
        and (rest or subcommand in GIT_LISTS_WHEN_BARE)
        and all(word in GIT_LISTS[subcommand] for word in rest)
    ):
        return
    if subcommand == "config" and any(word in GIT_CONFIG_READS for word in rest):
        return
    if subcommand == "clone":
        sources = without_values(rest, GIT_CLONE_VALUE_OPTIONS)
        if len(sources) > 1:
            target = sources[1]
        else:
            target = (
                sources[0].rstrip("/").rsplit("/", 1)[-1].removesuffix(".git")
                if sources
                else "."
            )
        check_targets(
            caller, tool_name, [target], ShellState(repository, state.variables)
        )
        return
    if repository is None:
        refuse(
            caller,
            tool_name,
            f"git {subcommand} changes a repository this guard cannot locate.",
        )
    if is_inside(repository, PROJECT_DIR):
        refuse(caller, tool_name, f"git {subcommand} changes the project repository.")
    if not is_scratch(repository):
        refuse(
            caller,
            tool_name,
            f"git {subcommand} changes {repository}, outside the scratch folder.",
        )
