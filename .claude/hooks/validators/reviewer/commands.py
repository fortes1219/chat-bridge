"""Which commands the reviewer may run: not what the project has built, not a model, not an
installer; only reading subcommands of the tools that also run things; and the checks, as they are
run here."""

from __future__ import annotations

from utils.roles import Caller
from utils.shell.words import positionals

from validators.reviewer.refusal import refuse

# Commands that use what the project has built, or a model, refused by name.
PROJECT_COMMANDS = {
    "chat-bridge": "starts the project",
    "pytest": "runs the tests",
    "claude": "starts a model CLI",
    "codex": "starts a model CLI",
    "psql": "uses the database",
    "pg_ctl": "uses the database",
    "postgres": "uses the database",
    "initdb": "uses the database",
    "uvx": "runs a tool through uv",
    "npx": "runs JavaScript tooling",
    "node": "runs JavaScript",
    "bun": "runs JavaScript",
    "deno": "runs JavaScript",
}
# Commands allowed only with these subcommands, which read. Two words where the first is a group.
READING_SUBCOMMANDS = {
    "uv": (
        {"--version", "-V", "version", "tree"},
        {"pip": {"list", "show", "freeze"}},
        "runs uv, which installs and runs the project",
    ),
    "docker": (
        {"ps", "images", "info", "version"},
        {
            "image": {"ls"},
            "container": {"ls"},
            "volume": {"ls"},
            "network": {"ls"},
            "system": {"df"},
        },
        "runs or changes containers, images or volumes",
    ),
    "docker-compose": (
        {"ps", "images", "version", "ls"},
        {},
        "runs or changes containers",
    ),
    "npm": (
        {"view", "info", "show", "search", "ls", "list", "outdated"},
        {},
        "runs JavaScript tooling",
    ),
    "pnpm": ({"view", "info", "ls", "list", "outdated"}, {}, "runs JavaScript tooling"),
    "yarn": ({"info", "list", "outdated"}, {}, "runs JavaScript tooling"),
}
INSTALLERS = {"pip", "pip3", "winget", "choco", "scoop"}
REFUSED_MODULES = {"chat_bridge", "pytest"}
INTERPRETERS = {
    "python",
    "python3",
    "py",
    "pythonw",
    "sh",
    "bash",
    "zsh",
    "dash",
    "pwsh",
    "powershell",
    "node",
    "deno",
    "bun",
    "ruby",
    "perl",
    "php",
    "source",
    ".",
}
INLINE_CODE_FLAGS = {"-c", "-e", "-command", "-encodedcommand", "-m"}
INTERPRETER_VALUE_FLAGS = {"-w", "-x"}

# The checks the reviewer may run, as they are run here. `--no-sync` keeps uv from installing
# anything; the container is the documented slow-test run, with nothing mounted or replaced.
CHECK_TOOLS = {"pytest", "ruff", "mypy"}
UV_RUN_OPTIONS = {"--no-sync", "-q", "--quiet"}
TEST_COMPOSE_FILE = "compose.test.yml"
TEST_SERVICE = "slow-tests"
TEST_RUN_OPTIONS = {"--rm", "-T"}


def check_command_use(
    caller: Caller, tool_name: str, name: str, arguments: list[str]
) -> None:
    """Refuses a command that uses what the project has built, a model CLI, or an installer."""
    if name in PROJECT_COMMANDS:
        refuse(caller, tool_name, f"The command {PROJECT_COMMANDS[name]}.")
    if name in INSTALLERS and "install" in arguments:
        refuse(caller, tool_name, "The command installs packages.")
    if name in INTERPRETERS and "-m" in arguments[:-1]:
        module = arguments[arguments.index("-m") + 1].split(".")[0]
        if module in REFUSED_MODULES:
            refuse(caller, tool_name, f"The command runs the {module} module.")
        if module == "pip" and "install" in arguments:
            refuse(caller, tool_name, "The command installs packages.")
    if name not in READING_SUBCOMMANDS or is_check_run(name, arguments):
        return
    singles, groups, reason = READING_SUBCOMMANDS[name]
    words = positionals(arguments)
    first = words[0] if words else (arguments[0] if arguments else "")
    if first in singles or (
        first in groups and len(words) > 1 and words[1] in groups[first]
    ):
        return
    refuse(caller, tool_name, f"The command {reason}.")


def is_check_run(name: str, arguments: list[str]) -> bool:
    """Whether the command runs the project's tests or checks, and nothing else."""
    if name == "uv" and arguments[:2] == ["lock", "--check"]:
        return True
    if name == "uv" and arguments[:1] == ["run"]:
        index = 1
        while index < len(arguments) and arguments[index] in UV_RUN_OPTIONS:
            index += 1
        has_no_sync = "--no-sync" in arguments[1:index]
        return (
            has_no_sync and index < len(arguments) and arguments[index] in CHECK_TOOLS
        )
    if name == "docker" and arguments[:4] == [
        "compose",
        "-f",
        TEST_COMPOSE_FILE,
        "run",
    ]:
        index = 4
        while index < len(arguments) and arguments[index] in TEST_RUN_OPTIONS:
            index += 1
        return index < len(arguments) and arguments[index] == TEST_SERVICE
    return False


def script_argument(arguments: list[str]) -> str | None:
    """The script an interpreter runs, or None for inline code, a module or standard input."""
    index = 0
    while index < len(arguments):
        argument = arguments[index]
        lowered = argument.lower()
        if lowered in INLINE_CODE_FLAGS:
            return None
        if lowered == "-file":
            return arguments[index + 1] if index + 1 < len(arguments) else None
        if argument.startswith("-"):
            index += 2 if lowered in INTERPRETER_VALUE_FLAGS else 1
            continue
        return argument
    return None
