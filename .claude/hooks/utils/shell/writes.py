"""Which paths a simple command writes, by the command's name and arguments."""

from __future__ import annotations

from utils.shell.words import cmdlet_positionals, flag_values, positionals

# Targets that keep nothing.
DISCARD = {"/dev/null", "nul", "$null"}
# POSIX tools (and the PowerShell aliases of the same names): every path argument is changed,
# or only the last one is written.
CHANGES_EVERY_PATH = {
    "rm",
    "rmdir",
    "del",
    "erase",
    "rd",
    "unlink",
    "shred",
    "mkdir",
    "md",
    "touch",
    "truncate",
    "tee",
    "mv",
    "move",
    "ln",
    "install",
    "patch",
    "chmod",
    "chown",
}
WRITES_LAST_PATH = {"cp", "copy", "xcopy", "robocopy", "scp", "rsync"}
# PowerShell cmdlets, by which positional arguments they write. Parameter names ignore case.
CMDLET_WRITES_FIRST = {
    "set-content",
    "sc",
    "add-content",
    "ac",
    "out-file",
    "new-item",
    "ni",
    "clear-content",
    "clc",
    "export-csv",
    "remove-item",
    "ri",
}
CMDLET_WRITES_SECOND = {"copy-item", "cpi", "expand-archive"}
CMDLET_WRITES_ALL = {"move-item", "mi", "rename-item", "rni"}
CMDLET_PATH_FLAGS = {
    "-path",
    "-literalpath",
    "-filepath",
    "-destination",
    "-destinationpath",
    "-outfile",
}
# Downloads: the flags that name the output, whether they ignore case, and whether the download
# lands in the working directory when no output is named.
DOWNLOADS = {
    "curl": ({"-o", "--output", "--output-dir"}, False, False),
    "wget": ({"-O", "-P", "--output-document", "--directory-prefix"}, False, True),
    "invoke-webrequest": ({"-outfile"}, True, False),
    "iwr": ({"-outfile"}, True, False),
    "invoke-restmethod": ({"-outfile"}, True, False),
    "irm": ({"-outfile"}, True, False),
}
CURL_REMOTE_NAME = {"-O", "--remote-name", "--remote-name-all"}


def write_targets(name: str, arguments: list[str]) -> list[str]:
    """The paths a simple command writes; '.' stands for the working directory."""
    if name in CHANGES_EVERY_PATH:
        return positionals(arguments) or ["."]
    if name in WRITES_LAST_PATH:
        return (
            flag_values(arguments, {"-t", "--target-directory"})
            or positionals(arguments)[-1:]
            or ["."]
        )
    named = flag_values(arguments, CMDLET_PATH_FLAGS, ignore_case=True)
    if name in CMDLET_WRITES_FIRST:
        return named + cmdlet_positionals(arguments)[:1] or ["."]
    if name in CMDLET_WRITES_SECOND:
        return named + cmdlet_positionals(arguments)[1:2] or ["."]
    if name in CMDLET_WRITES_ALL:
        return named + cmdlet_positionals(arguments) or ["."]
    if name in {"sed", "perl"} and any(
        argument.startswith("-i") or argument == "--in-place" for argument in arguments
    ):
        return positionals(arguments)[1:] or ["."]
    if name == "find" and any(
        argument in {"-delete", "-exec", "-execdir", "-ok", "-okdir", "-fprint"}
        for argument in arguments
    ):
        return positionals(arguments)[:1] or ["."]
    if name in DOWNLOADS:
        flags, ignore_case, lands_here = DOWNLOADS[name]
        outputs = flag_values(arguments, flags, ignore_case)
        if name == "curl" and any(
            argument in CURL_REMOTE_NAME for argument in arguments
        ):
            outputs.append(".")
        return outputs or (["."] if lands_here else [])
    if name == "unzip":
        return flag_values(arguments, {"-d"}) or ["."]
    if name == "tar" and arguments and "x" in arguments[0]:
        return flag_values(arguments, {"-C", "--directory"}) or ["."]
    if name == "dd":
        return [argument[3:] for argument in arguments if argument.startswith("of=")]
    return []
