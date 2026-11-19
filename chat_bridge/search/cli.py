"""The `chat-bridge search <question>` subcommand."""

import argparse
import asyncio

from chat_bridge.cli import EXIT_NOT_ALL, EXIT_OK, Commands, print_error
from chat_bridge.search import service as search_service
from chat_bridge.tokenizer import DictionaryError

# Errors that come from the user's data or environment, with what to tell them.
KNOWN_ERRORS: dict[type[Exception], str] = {
    search_service.EmptyKnowledgeBaseError: "the knowledge base is empty; run `chat-bridge ingest <folder>` first",
    search_service.IndexMismatchError: (
        "the search index was built with another dictionary or other keywords; "
        "run `chat-bridge ingest <folder>` again"
    ),
}

# The same range MaxKB allows for its search's top_number (1 to 10000). Without an upper
# bound, a number past PostgreSQL's bigint reaches LIMIT and fails inside the database.
MIN_LIMIT = 1
MAX_LIMIT = 10_000


def _limit(value: str) -> int:
    """Parse --limit at the command-line boundary. argparse turns ArgumentTypeError into
    a one-line usage error with exit code 2, before the database starts."""
    try:
        number = int(value)
    except ValueError:
        raise argparse.ArgumentTypeError(f"not a whole number: {value!r}") from None
    if not MIN_LIMIT <= number <= MAX_LIMIT:
        raise argparse.ArgumentTypeError(
            f"must be from {MIN_LIMIT} to {MAX_LIMIT}, got {number}"
        )
    return number


def _run(args: argparse.Namespace) -> int:
    try:
        result = asyncio.run(search_service.search(args.question, args.limit))
    except DictionaryError as error:
        return print_error(str(error))
    except tuple(KNOWN_ERRORS) as error:
        return print_error(KNOWN_ERRORS[type(error)])

    if not result.query:
        print(f"Not in the data: the question has no searchable word: {args.question}")
        return EXIT_NOT_ALL
    if not result.hits:
        print(f"Not in the data: no section matches: {args.question}")
        return EXIT_NOT_ALL

    print(f"Query: {result.query}")
    for number, hit in enumerate(result.hits, start=1):
        heading = f" > {hit.heading}" if hit.heading else ""
        print(f"{number}. {hit.source_path}{heading}  (rank {hit.rank:.3f})")
        print(f"   {hit.title}")
        print(f"   {hit.snippet}")
    return EXIT_OK


def register(commands: Commands) -> None:
    search = commands.add_parser(
        "search", help="list the stored sections that match a question"
    )
    search.add_argument(
        "question", help="the question, in Traditional Chinese or English"
    )
    search.add_argument(
        "--limit", type=_limit, default=5, help="how many sections to list (default: 5)"
    )
    search.set_defaults(handler=_run)
