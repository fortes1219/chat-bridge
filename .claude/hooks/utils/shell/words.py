"""A shell command split into simple commands, and the arguments of each."""

from __future__ import annotations

import re
import shlex

SEPARATOR_CHARS = set(";&|()\n")
REDIRECTS = {">", ">>", ">|", "&>", "&>>"}
REDIRECTION_WORDS = REDIRECTS | {"<<", "<<-", "<", ">&", "<&"}
# Words that only introduce the command after them.
PREFIX_WORDS = {
    "do",
    "then",
    "else",
    "elif",
    "if",
    "while",
    "until",
    "time",
    "!",
    "{",
    "env",
    "nohup",
    "command",
    "builtin",
    "exec",
    "nice",
    "xargs",
    "sudo",
}
BASH_HEREDOC_BODY = re.compile(
    r'(<<-?[ \t]*([\'"]?)(\w+)\2[^\n]*)\n.*?\n[ \t]*\3[ \t]*(?=\n|$)', re.DOTALL
)
POWERSHELL_HERE_STRING = re.compile(r'@([\'"])\r?\n.*?\r?\n\1@', re.DOTALL)
# PowerShell parameters that take no value, so the word after them is a positional argument.
CMDLET_SWITCHES = {
    "-force",
    "-recurse",
    "-nonewline",
    "-append",
    "-whatif",
    "-confirm",
    "-passthru",
    "-noclobber",
}


def command_segments(command: str) -> list[list[str]] | None:
    """The command split into simple commands, with heredoc and here-string bodies left out."""
    text = POWERSHELL_HERE_STRING.sub("''", BASH_HEREDOC_BODY.sub(r"\1", command))
    lexer = shlex.shlex(text, posix=True, punctuation_chars=";&|()<>\n")
    lexer.whitespace = " \t\r"
    lexer.whitespace_split = True
    lexer.commenters = ""
    lexer.escape = ""  # Windows paths use backslashes
    try:
        tokens = list(lexer)
    except ValueError:
        return None
    segments: list[list[str]] = [[]]
    for token in tokens:
        if set(token) <= SEPARATOR_CHARS:
            segments.append([])
            continue
        segments[-1].append(token)
    return [words for words in segments if words]


def command_name(word: str) -> str:
    name = word.replace("\\", "/").rsplit("/", 1)[-1].lower()
    for suffix in (".exe", ".cmd", ".bat"):
        name = name.removesuffix(suffix)
    return name


def strip_prefixes(words: list[str]) -> list[str]:
    index = 0
    while index < len(words) and (
        words[index].lower() in PREFIX_WORDS or re.match(r"^\w+=", words[index])
    ):
        index += 1
    return words[index:]


def is_redirection(words: list[str], index: int) -> bool:
    if words[index] in REDIRECTION_WORDS:
        return True
    if index > 0 and words[index - 1] in REDIRECTION_WORDS:
        return True
    # The descriptor number before a redirection, as in 2>/dev/null.
    return (
        words[index].isdigit()
        and index + 1 < len(words)
        and words[index + 1] in REDIRECTION_WORDS
    )


def positionals(arguments: list[str]) -> list[str]:
    return [argument for argument in arguments if not argument.startswith("-")]


def flag_values(
    arguments: list[str], flags: set[str], ignore_case: bool = False
) -> list[str]:
    """The values given to these flags, as `-o value` or `--output=value`."""
    values = []
    for index, argument in enumerate(arguments):
        key = argument.lower() if ignore_case else argument
        if key in flags and index + 1 < len(arguments):
            values.append(arguments[index + 1])
        name, _, value = key.partition("=")
        if value and name in flags and name.startswith("--"):
            values.append(argument.split("=", 1)[1])
    return values


def without_values(arguments: list[str], value_options: set[str]) -> list[str]:
    """Positional arguments, skipping each option and the value it takes."""
    found = []
    index = 0
    while index < len(arguments):
        argument = arguments[index]
        if argument.startswith("-"):
            index += 2 if argument in value_options else 1
            continue
        found.append(argument)
        index += 1
    return found


def cmdlet_positionals(arguments: list[str]) -> list[str]:
    """PowerShell: the arguments that are neither parameters nor their values."""
    found = []
    index = 0
    while index < len(arguments):
        argument = arguments[index]
        if argument.startswith("-"):
            index += 1 if argument.lower() in CMDLET_SWITCHES or ":" in argument else 2
            continue
        found.append(argument)
        index += 1
    return found
