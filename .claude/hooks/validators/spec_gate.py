"""Code waits for its spec.

The project follows Spec Kit, so a repository file can only be edited once the feature in progress
(.specify/feature.json) has a spec, a plan and a task list, and neither the spec nor the plan still
carries a [NEEDS CLARIFICATION] marker: the same prerequisites Spec Kit's own check-prerequisites
script asks for before the implement step.

Its research.md must also have a complete "## Packages" table (constitution I): every need names
an installable package, its license (not GPL or AGPL), its size, and a project that depends on it
and calls it, cited as owner/repo@commit:path:line. A need with no package, or not looked up yet,
stops the writer, who reports it to the Owner instead of writing it by hand.

The spec artifacts themselves (.specify/ and specs/) can always be edited.
"""

from __future__ import annotations

import json
import re
from pathlib import Path

from utils.places import PROJECT_DIR, is_inside

SPECIFY_DIR = PROJECT_DIR / ".specify"
SPECS_DIR = PROJECT_DIR / "specs"
FEATURE_POINTER = SPECIFY_DIR / "feature.json"
SPEC_FILE = "spec.md"
PLAN_FILE = "plan.md"
TASKS_FILE = "tasks.md"
RESEARCH_FILE = "research.md"
OPEN_CLARIFICATION = "[NEEDS CLARIFICATION"

PACKAGES_HEADING = re.compile(r"^##\s+Packages\s*$", re.IGNORECASE | re.MULTILINE)
PACKAGE_COLUMNS = (
    "need",
    "package",
    "version",
    "license",
    "size",
    "dependency declared in",
    "called in",
)
CITED_COLUMNS = ("dependency declared in", "called in")
CITATION = re.compile(r"[\w.-]+/[\w.-]+@[0-9a-f]{7,40}:[^\s:;|`]+:\d+(?:-\d+)?")
COPYLEFT = re.compile(r"\bA?GPL", re.IGNORECASE)  # GPL and AGPL; LGPL does not match
NO_PACKAGE = {"none", "-", "n/a"}
TABLE_SEPARATOR = re.compile(r"^:?-+:?$")
REPORT_TO_OWNER = (
    "Stop and report to the Owner: which need has no installable package or has not been "
    "looked up yet, and what you checked. Do not write it by hand."
)


def is_spec_artifact(path: Path) -> bool:
    return is_inside(path, SPECIFY_DIR) or is_inside(path, SPECS_DIR)


def feature_in_progress() -> tuple[Path | None, str]:
    """The feature directory .specify/feature.json points at, or None with the reason it has none."""
    if not FEATURE_POINTER.is_file():
        return (
            None,
            "no feature is in progress (.specify/feature.json is missing); write its spec first",
        )
    # PowerShell writes this file and may put a byte order mark in front.
    pointer = json.loads(FEATURE_POINTER.read_text(encoding="utf-8-sig"))
    raw = pointer.get("feature_directory") if isinstance(pointer, dict) else None
    if not isinstance(raw, str) or not raw.strip():
        return None, ".specify/feature.json names no feature_directory"
    path = Path(raw)
    feature_dir = (path if path.is_absolute() else PROJECT_DIR / path).resolve()
    if not is_inside(feature_dir, PROJECT_DIR) or not feature_dir.is_dir():
        return None, f"the feature directory {raw} does not exist inside the project"
    return feature_dir, ""


def implementation_refusal(feature_dir: Path) -> str | None:
    """Why the feature is not ready for code edits, or None when it is."""
    name = feature_dir.relative_to(PROJECT_DIR).as_posix()
    texts: dict[str, str] = {}
    for artifact in (SPEC_FILE, PLAN_FILE, TASKS_FILE):
        path = feature_dir / artifact
        texts[artifact] = path.read_text(encoding="utf-8-sig") if path.is_file() else ""
    missing = [artifact for artifact, text in texts.items() if not text.strip()]
    if missing:
        return f"{name} has no {', '.join(missing)} yet; finish the specify, plan and tasks steps first"
    unanswered = [
        artifact
        for artifact in (SPEC_FILE, PLAN_FILE)
        if OPEN_CLARIFICATION in texts[artifact]
    ]
    if unanswered:
        return f"{name}: {', '.join(unanswered)} still has a [NEEDS CLARIFICATION] marker; it is the Owner's to answer"
    return None


def table_rows(text: str) -> list[list[str]]:
    """The cells of the first Markdown table in the text, header first, separator row left out."""
    rows: list[list[str]] = []
    for line in text.splitlines():
        stripped = line.strip()
        if not stripped.startswith("|"):
            if rows or stripped.startswith("#"):
                break
            continue
        cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        if not all(TABLE_SEPARATOR.match(cell) for cell in cells):
            rows.append(cells)
    return rows


def package_problems(cells: list[str]) -> list[str]:
    if len(cells) != len(PACKAGE_COLUMNS):
        return [f"a row has {len(cells)} cells instead of {len(PACKAGE_COLUMNS)}"]
    row = dict(zip(PACKAGE_COLUMNS, cells, strict=True))
    need = row["need"] or "(unnamed need)"
    if row["package"].strip("`").lower() in NO_PACKAGE:
        return [f'"{need}" has no package']
    empty = [column for column in PACKAGE_COLUMNS if not row[column]]
    if empty:
        return [f'"{need}" leaves {", ".join(empty)} empty']
    problems = (
        [f'"{need}" uses a GPL or AGPL package']
        if COPYLEFT.search(row["license"])
        else []
    )
    problems += [
        f'"{need}": {column} is not owner/repo@commit:path:line'
        for column in CITED_COLUMNS
        if not CITATION.search(row[column])
    ]
    return problems


def package_table_refusal(feature_dir: Path) -> str | None:
    """Why research.md does not yet show an installable, cited package for every need, or None."""
    name = f"{feature_dir.relative_to(PROJECT_DIR).as_posix()}/{RESEARCH_FILE}"
    path = feature_dir / RESEARCH_FILE
    text = path.read_text(encoding="utf-8-sig") if path.is_file() else ""
    if not text.strip():
        return f"{name} does not exist yet"
    if OPEN_CLARIFICATION in text:
        return f"{name} still has a [NEEDS CLARIFICATION] marker"
    heading = PACKAGES_HEADING.search(text)
    if heading is None:
        return f'{name} has no "## Packages" table'
    rows = table_rows(text[heading.end() :])
    if not rows or [cell.lower() for cell in rows[0]] != list(PACKAGE_COLUMNS):
        return f"the Packages table in {name} must have the columns: {' | '.join(PACKAGE_COLUMNS)}"
    if len(rows) == 1:
        return f"the Packages table in {name} has no rows"
    problems = [problem for cells in rows[1:] for problem in package_problems(cells)]
    return f"the Packages table in {name}: {'; '.join(problems)}" if problems else None


def repository_refusal(relative_path: str) -> str | None:
    """Why a repository file outside the spec artifacts cannot be written yet, or None."""
    feature_dir, reason = feature_in_progress()
    if feature_dir is None:
        return f"{relative_path} cannot be edited: {reason}."
    refusal = implementation_refusal(feature_dir)
    if refusal is not None:
        return f"{relative_path} cannot be edited: {refusal}."
    missing = package_table_refusal(feature_dir)
    if missing is not None:
        return f"{relative_path} cannot be edited: {missing}. {REPORT_TO_OWNER}"
    return None
