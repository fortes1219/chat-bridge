"""The chat page: built with the reader's own Node.js, then served by the chat service.

`frontend/` holds the page's source. `uv run chat-bridge` builds it into `frontend/dist`
(git-ignored) when there is no build yet or a source changed since the last one, so a reader
runs one command and nothing is built in advance.
"""

import hashlib
import logging
import os
import re
import shutil
import subprocess
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from chat_bridge.config import PROJECT_ROOT
from chat_bridge.errors import LocalSetupError

logger = logging.getLogger(__name__)

FRONTEND = PROJECT_ROOT / "frontend"
BUILD_FOLDER = "dist"
PACKAGES_FOLDER = "node_modules"
LOCK_FILE = "package-lock.json"
# Not sources: what the install writes and what the build writes.
NOT_SOURCES = frozenset({PACKAGES_FOLDER, BUILD_FOLDER})
# Written into the build after the build succeeds, so a build that stopped halfway is done
# again on the next run.
STAMP_FILE = ".sources-sha256"
# Written into node_modules after an install succeeds: the lock file it installed from.
INSTALL_STAMP_FILE = ".chat-bridge-lock-sha256"
# `install` updates node_modules in place. `ci` deletes it first, and on Windows that fails
# whenever any program has one of its native modules loaded, such as a dev server or a test
# run. The lock file pins every version either way. Install scripts stay off: the packages were
# checked with them off, and the one package that has one only rewrites files for Vue 2.
NPM_INSTALL = ("install", "--ignore-scripts", "--no-audit", "--no-fund")
NPM_BUILD = ("run", "build")
# Windows reports a failed process's negative exit code as an unsigned 32-bit number.
UNSIGNED_EXIT_CODES = 2**32

# The Node.js lines that still get security fixes, each with its latest security release
# (nodejs.org/dist/index.json and endoflife.date, checked 2026-11-22). An older Node.js
# would build the page with known flaws, so it is refused by name instead of used.
NODE_MINIMUMS: dict[int, tuple[int, int, int]] = {
    22: (22, 23, 5),
    24: (24, 22, 3),
    26: (26, 13, 1),
}
NODE_VERSION = re.compile(r"^v(\d+)\.(\d+)\.(\d+)$")

# The service's own paths. An unknown address under them is a 404, so a wrong request from the
# page is not answered with the page itself.
SERVICE_PATHS = frozenset({"chat"})


def _version_text(version: tuple[int, int, int]) -> str:
    return ".".join(str(part) for part in version)


SUPPORTED_NODE = ", ".join(_version_text(low) for low in NODE_MINIMUMS.values())
INSTALL_NODE = (
    f"Install Node.js {SUPPORTED_NODE} or later in the same line, "
    "then run the command again."
)


def check_node(reported: str) -> None:
    """Refuse a Node.js that is not at the latest security release of a supported line.

    A line newer than every line in NODE_MINIMUMS came out after the table was checked, so
    nothing is known against it and it is used.
    """
    found = NODE_VERSION.match(reported.strip())
    if found is None:
        raise LocalSetupError(
            f"Could not read the Node.js version from {reported.strip()!r}. {INSTALL_NODE}"
        )
    version = (int(found[1]), int(found[2]), int(found[3]))
    if version[0] > max(NODE_MINIMUMS):
        return
    minimum = NODE_MINIMUMS.get(version[0])
    if minimum is None:
        raise LocalSetupError(
            f"Node.js {_version_text(version)} no longer gets security fixes. {INSTALL_NODE}"
        )
    if version < minimum:
        raise LocalSetupError(
            f"Node.js {_version_text(version)} lacks security fixes that "
            f"{_version_text(minimum)} has. Install Node.js {_version_text(minimum)} or "
            "later, then run the command again."
        )


def _program(name: str) -> str:
    """`node` or `npm` as found on PATH.

    On Windows the search looks in the current folder first, so a program of the same name put
    in the folder the service runs from would be found before the user's own. Such a program
    is refused, never run, as the Codex lookup does.
    """
    found = shutil.which(name)
    if found is None:
        raise LocalSetupError(
            f"The chat page is built with Node.js, and `{name}` was not found. {INSTALL_NODE}"
        )
    if Path(found).resolve().is_relative_to(Path.cwd().resolve()):
        raise LocalSetupError(
            f"The `{name}` found is in the folder the service runs from, so it is not run: "
            f"{found}"
        )
    return found


def sources_digest(frontend: Path) -> str:
    """SHA-256 over the name and content of every source file, in a fixed order."""
    files: list[Path] = []
    for folder, subfolders, names in os.walk(frontend):
        # Pruned in place, so the walk never enters node_modules.
        subfolders[:] = sorted(name for name in subfolders if name not in NOT_SOURCES)
        files.extend(Path(folder) / name for name in sorted(names))
    digest = hashlib.sha256()
    for path in files:
        digest.update(path.relative_to(frontend).as_posix().encode())
        digest.update(b"\0")
        digest.update(path.read_bytes())
        digest.update(b"\0")
    return digest.hexdigest()


def _exit_code(returncode: int) -> int:
    return returncode - UNSIGNED_EXIT_CODES if returncode >= 2**31 else returncode


def _run_npm(npm: str, args: tuple[str, ...], frontend: Path) -> None:
    # npm's own output goes to the terminal, so the reader sees what it is doing and why it
    # failed.
    done = subprocess.run([npm, *args], cwd=frontend, check=False)
    if done.returncode != 0:
        raise LocalSetupError(
            f"`npm {' '.join(args)}` failed with exit code {_exit_code(done.returncode)}; "
            "its output is above. If it says a file is in use, close what is using "
            f"{frontend.name}/{PACKAGES_FOLDER}, such as a dev server or a test run, and run "
            "the command again."
        )


def _file_digest(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _install_if_needed(npm: str, frontend: Path) -> None:
    """Install the locked packages when node_modules is missing or the lock file changed."""
    lock_digest = _file_digest(frontend / LOCK_FILE)
    stamp = frontend / PACKAGES_FOLDER / INSTALL_STAMP_FILE
    if stamp.is_file() and stamp.read_text(encoding="utf-8").strip() == lock_digest:
        return
    _run_npm(npm, NPM_INSTALL, frontend)
    stamp.write_text(lock_digest + "\n", encoding="utf-8", newline="\n")


def prepare_page(frontend: Path = FRONTEND) -> Path:
    """The folder of the built page, built first when it is missing or out of date."""
    for name in ("package.json", LOCK_FILE):
        if not (frontend / name).is_file():
            raise LocalSetupError(
                f"The chat page's source is missing: {frontend / name}"
            )
    dist = frontend / BUILD_FOLDER
    stamp = dist / STAMP_FILE
    digest = sources_digest(frontend)
    if stamp.is_file() and stamp.read_text(encoding="utf-8").strip() == digest:
        return dist

    node = _program("node")
    reported = subprocess.run(
        [node, "--version"], capture_output=True, text=True, check=False
    ).stdout
    check_node(reported)
    npm = _program("npm")
    logger.info(
        "Building the chat page with Node.js %s; this runs once.", reported.strip()
    )
    _install_if_needed(npm, frontend)
    _run_npm(npm, NPM_BUILD, frontend)
    stamp.write_text(digest + "\n", encoding="utf-8", newline="\n")
    return dist


def mount_page(app: FastAPI, dist: Path) -> None:
    """Serve the built page at `/`.

    A file of the build is sent as it is. Any other address gets `index.html`, so the page can
    keep its state in the address and a reload still opens it.
    """
    root = dist.resolve()
    index = root / "index.html"
    app.mount("/assets", StaticFiles(directory=root / "assets"), name="page-assets")

    @app.get("/{path:path}", include_in_schema=False)
    async def page(path: str) -> FileResponse:
        if path.split("/", 1)[0] in SERVICE_PATHS:
            raise HTTPException(status_code=404)
        file = (root / path).resolve()
        # A path that leads out of the build, such as one with "..", gets the page instead.
        if path and file.is_file() and file.is_relative_to(root):
            return FileResponse(file)
        return FileResponse(index)
