"""Shell rules for every role: every command is logged; only the Owner commits and pushes;
installs, repository state changes and sending data out are his to approve."""

from __future__ import annotations

import re

from utils.decision import ask_and_log, decide, log
from utils.roles import Caller
from utils.shell.paths import ShellState
from utils.shell.reading import read_segment
from utils.shell.words import command_segments, positionals

# (pattern, decision, reason). First match wins, so deny rules come first.
SHELL_RULES: tuple[tuple[re.Pattern[str], str, str], ...] = (
    (
        re.compile(r"\bgit\b[^|;&\n]*\b(commit|push)\b"),
        "deny",
        "Only the Owner commits and pushes.",
    ),
    (
        re.compile(
            r"\b(uv\s+(add|remove|sync|lock|pip\s+install|tool|python\s+install)|pip3?\s+install|"
            r"python\S*\s+-m\s+pip\s+install|(npm|pnpm|yarn|bun)\s+(i|install|add|remove|ci)\b|"
            r"npx\s|(winget|choco|scoop)\s+install|claude\s+update)"
        ),
        "ask",
        "Installs or changes dependencies on the Owner's machine.",
    ),
    (
        re.compile(
            r"\bgit\b[^|;&\n]*\b(add|rm|mv|restore|checkout|switch|reset|clean|stash|merge|rebase|"
            r"cherry-pick|revert|tag|branch\s+-[dDmM])\b"
        ),
        "ask",
        "Changes the repository state.",
    ),
)

# Flags that send a body or a file. PowerShell parameter names ignore case.
SENDS_DATA = {
    "curl": {
        "-d",
        "--data",
        "--data-raw",
        "--data-binary",
        "--data-urlencode",
        "--data-ascii",
        "--json",
        "-F",
        "--form",
        "--form-string",
        "-T",
        "--upload-file",
    },
    "wget": {"--post-data", "--post-file", "--body-data", "--body-file"},
    "invoke-webrequest": {"-body", "-infile"},
    "iwr": {"-body", "-infile"},
    "invoke-restmethod": {"-body", "-infile"},
    "irm": {"-body", "-infile"},
}
# Flags that name the HTTP method; any method but these reads.
METHOD_FLAGS = {"-X", "--request", "--method", "-method"}
READING_METHODS = {"get", "head", "options"}
POWERSHELL_FETCHES = {"invoke-webrequest", "iwr", "invoke-restmethod", "irm"}
# curl's short flags can be glued together and to their value (`-sXPOST`, `-d@notes.txt`). These
# send; X names the method; the others take a value, so the rest of the word is that value.
CURL_SENDING_LETTERS = set("dFT")
CURL_VALUE_LETTERS = set("oHuAebcrwxmKCEYyzPQtUD")
# Copying to another machine: `host:path` or `user@host:path` (a one-letter host is a drive).
REMOTE_COPIES = {"scp", "rsync", "sftp"}
REMOTE_PATH = re.compile(r"^([\w.-]+@)?[\w.-]{2,}:")
# GitHub CLI: `gh api` sends with a method or fields; any other subcommand that is not one of
# these reads creates or changes something on GitHub.
GH_READS = {
    "view",
    "list",
    "status",
    "diff",
    "checks",
    "search",
    "browse",
    "--version",
    "version",
}
GH_API_SENDING = {"-f", "-F", "--field", "--raw-field", "--input"}
# Publishing a package or an image: sent out for good.
PUBLISHES = {
    "npm": "publish",
    "pnpm": "publish",
    "yarn": "publish",
    "uv": "publish",
    "poetry": "publish",
    "cargo": "publish",
    "twine": "upload",
    "docker": "push",
}
# Where sending is not asked about: this machine's own services, such as the app under test, and
# the vulnerability lookups the constitution asks for, which send only package names and versions
# from the public lock files.
KNOWN_URL = re.compile(
    r"^(https?://(localhost|127\.0\.0\.1|\[::1\])(:\d+)?|https://api\.osv\.dev)(/|$)",
    re.IGNORECASE,
)
URL = re.compile(r"^https?://", re.IGNORECASE)
# A command too tangled to read is still asked about when its text names a sending flag.
SENDING_TEXT = re.compile(
    r"\b(curl|wget|Invoke-WebRequest|Invoke-RestMethod|iwr|irm)\b[^|;&\n]*\s"
    r"(-d|--data\S*|--json|-F|--form\S*|-T|--upload-file|--post-\S+|--body-\S+|-Body|-InFile|"
    r"-X\s*(POST|PUT|PATCH|DELETE)|--request\s*(POST|PUT|PATCH|DELETE)|-Method\s+(Post|Put|Patch|Delete))\b"
    r"|\b(ssh|scp|sftp)\s|\bgh\s+(api|gist|issue|pr|release|repo)\b",
    re.IGNORECASE,
)


def record(caller: Caller, tool_name: str, command: str) -> None:
    """Writes every shell command to the log, whatever the answer, so what ran can be read back."""
    lines = command.strip().splitlines()
    first = lines[0][:300] if lines else ""
    more = f" (+{len(lines) - 1} lines)" if len(lines) > 1 else ""
    log(caller, tool_name, f"run: {first}{more}")


def stop_commits(command: str) -> None:
    """Refuses a commit or a push, whoever asks."""
    for pattern, decision, reason in SHELL_RULES:
        if decision == "deny" and pattern.search(command):
            decide(decision, reason)


def ask_before_changes(command: str) -> None:
    """Puts an install or a repository state change in front of the Owner."""
    for pattern, decision, reason in SHELL_RULES:
        if pattern.search(command):
            decide(decision, reason)


def ask_before_uploads(caller: Caller, tool_name: str, command: str) -> None:
    """Puts a command that sends data to another machine in front of the Owner."""
    segments = command_segments(command)
    if segments is None:
        if SENDING_TEXT.search(command):
            ask_and_log(
                caller, tool_name, "A command the guard cannot read sends data out."
            )
        return
    state = ShellState(caller.cwd, {})
    for words in segments:
        read = read_segment(words, state)
        if read is None or not read[1]:
            continue
        name, words, _ = read
        if sends_data(name, words[1:]) and not only_known_hosts(words[1:]):
            ask_and_log(
                caller, tool_name, f"{words[0]} sends data out: {' '.join(words)[:200]}"
            )


def sends_data(name: str, arguments: list[str]) -> bool:
    if name == "ssh":
        return True
    if name in PUBLISHES:
        return PUBLISHES[name] in positionals(arguments)[:1]
    if name in REMOTE_COPIES:
        return any(REMOTE_PATH.match(argument) for argument in arguments)
    if name == "gh":
        return gh_sends(arguments)
    flags = SENDS_DATA.get(name)
    if flags is None:
        return False
    if name == "curl" and any(
        curl_cluster_sends(argument, arguments[index + 1 : index + 2])
        for index, argument in enumerate(arguments)
    ):
        return True
    for index, argument in enumerate(arguments):
        key = argument.split("=", 1)[0]
        key = key.lower() if name in POWERSHELL_FETCHES else key
        if key in flags:
            return True
        method = (
            argument.split("=", 1)[1]
            if "=" in argument
            else (arguments[index + 1] if index + 1 < len(arguments) else "")
        )
        if key in METHOD_FLAGS and method.strip("'\"").lower() not in READING_METHODS:
            return True
    return False


def curl_cluster_sends(argument: str, following: list[str]) -> bool:
    """Whether one of curl's glued short flags sends: `-d@x`, `-sF a=b`, `-XPOST`, `-sX POST`."""
    if not argument.startswith("-") or argument.startswith("--") or len(argument) < 2:
        return False
    letters = argument[1:]
    for index, letter in enumerate(letters):
        if letter in CURL_SENDING_LETTERS:
            return True
        if letter == "X":
            method = letters[index + 1 :] or (following[0] if following else "")
            return method.strip("'\"").lower() not in READING_METHODS
        if letter in CURL_VALUE_LETTERS:
            return False
    return False


def gh_sends(arguments: list[str]) -> bool:
    words = [argument for argument in arguments if not argument.startswith("-")]
    if not words or words[0] in GH_READS:
        return False
    if words[:1] == ["api"]:
        # A method named outright decides; with GET the fields are the query string.
        for index, argument in enumerate(arguments):
            key, _, value = argument.partition("=")
            if key in {"-X", "--method"}:
                method = value or (
                    arguments[index + 1] if index + 1 < len(arguments) else ""
                )
                return method.strip("'\"").lower() not in READING_METHODS
        # Without one, gh sends fields as a POST.
        return any(
            argument.split("=", 1)[0] in GH_API_SENDING for argument in arguments
        )
    return len(words) >= 2 and words[1] not in GH_READS


def only_known_hosts(arguments: list[str]) -> bool:
    urls = [
        argument.strip("'\"")
        for argument in arguments
        if URL.match(argument.strip("'\""))
    ]
    return bool(urls) and all(KNOWN_URL.match(url) for url in urls)
