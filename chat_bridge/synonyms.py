"""The synonym table: names that mean the same thing.

The file uses the Solr synonyms format that Lucene's SolrSynonymParser reads: one group of
equivalent names per line, separated by commas; empty lines and lines that start with "#"
are comments. Only equivalent names are read. An explicit mapping ("a => b") is refused.

As in RAGFlow, synonyms are used when searching: a question that mentions a name also
searches for the other names in its group. Every name is also a jieba user word, on the
index side and the query side, as MaxKB loads its term base, so a name is never cut apart.
"""

import itertools
from dataclasses import dataclass
from pathlib import Path

from chat_bridge.config import PROJECT_ROOT
from chat_bridge.errors import LocalSetupError
from chat_bridge.tokenizer import mentions

SYNONYMS_PATH = PROJECT_ROOT / "data" / "synonyms.txt"
COMMENT_MARK = "#"
EXPLICIT_MAPPING = "=>"
# RAGFlow's synonym lookup returns at most 8 names for one word.
MAX_SYNONYMS_PER_GROUP = 8


class SynonymFileError(LocalSetupError):
    """The synonym file breaks the format. The message lists every problem with its line."""


@dataclass(frozen=True)
class SynonymGroup:
    line: int
    names: tuple[str, ...]


@dataclass(frozen=True)
class Synonyms:
    groups: tuple[SynonymGroup, ...]

    def names(self) -> list[str]:
        return [name for group in self.groups for name in group.names]

    def expand(self, question: str) -> list[str]:
        """The other names of every group the question mentions."""
        lowered = question.lower()
        found: list[str] = []
        for group in self.groups:
            others = [name for name in group.names if not mentions(lowered, name)]
            if len(others) == len(group.names):
                continue
            found.extend(others[:MAX_SYNONYMS_PER_GROUP])
        return found


def _line_problems(number: int, names: tuple[str, ...]) -> list[str]:
    if not all(names):
        return [f"line {number}: a name is empty"]
    if len(names) < 2:
        return [f"line {number}: a group needs at least two names"]
    return []


def _nested_names(groups: list[SynonymGroup]) -> list[str]:
    # A name inside a name of another group would expand both groups whenever the longer
    # name is mentioned, as "Fed" is inside "Fed funds rate". Such a pair is refused.
    names = [(group.line, name) for group in groups for name in group.names]
    return [
        f"line {inner_line}: {inner!r} is inside {outer!r} on line {outer_line}"
        for (inner_line, inner), (outer_line, outer) in itertools.product(
            names, repeat=2
        )
        if inner_line != outer_line
        and inner.lower() != outer.lower()  # a repeated name is reported once, above
        and mentions(outer.lower(), inner)
    ]


def load_synonyms(path: Path = SYNONYMS_PATH) -> Synonyms:
    """Read and check the synonym file. Every problem is reported at once, with its line."""
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except OSError as error:
        raise SynonymFileError(
            f"could not read the synonym file {path}: {error}"
        ) from error

    problems: list[str] = []
    groups: list[SynonymGroup] = []
    first_line_of: dict[str, int] = {}
    for number, line in enumerate(lines, start=1):
        if not line.strip() or line.startswith(COMMENT_MARK):
            continue
        if EXPLICIT_MAPPING in line:
            problems.append(
                f"line {number}: '{EXPLICIT_MAPPING}' mappings are not supported; "
                "list the equivalent names separated by commas"
            )
            continue
        names = tuple(name.strip() for name in line.split(","))
        line_problems = _line_problems(number, names)
        if line_problems:
            problems.extend(line_problems)
            continue
        for name in names:
            key = name.lower()
            if key in first_line_of:
                problems.append(
                    f"line {number}: {name!r} is already on line {first_line_of[key]}"
                )
                continue
            first_line_of[key] = number
        groups.append(SynonymGroup(number, names))

    problems.extend(_nested_names(groups))
    if problems:
        raise SynonymFileError(
            f"the synonym file {path} has {len(problems)} problem(s):\n  "
            + "\n  ".join(problems)
        )
    return Synonyms(tuple(groups))
