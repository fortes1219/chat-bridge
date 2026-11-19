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
        "--limit", type=int, default=5, help="how many sections to list (default: 5)"
    )
    search.set_defaults(handler=_run)
