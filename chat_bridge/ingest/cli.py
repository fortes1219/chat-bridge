"""The `chat-bridge ingest <folder>` subcommand."""

import argparse
import asyncio
from pathlib import Path

from chat_bridge.cli import EXIT_NOT_ALL, EXIT_OK, Commands, print_error
from chat_bridge.ingest import service as ingest_service
from chat_bridge.tokenizer import DictionaryError


def _run(args: argparse.Namespace) -> int:
    folder: Path = args.folder
    if not folder.is_dir():
        return print_error(f"not a folder: {folder}")
    try:
        report = asyncio.run(ingest_service.ingest_folder(folder.resolve()))
    except DictionaryError as error:
        return print_error(str(error))

    print(f"Written: {len(report.written)} files, {report.sections_written} sections.")
    print(f"Unchanged and skipped: {len(report.unchanged)} files.")
    if report.written or report.removed:
        index_note = (
            "rebuilt for every section"
            if report.reindexed_all
            else "updated for the written files"
        )
        print(f"Search index: {index_note}.")
    for path in report.removed:
        print(
            f"Removed the stored version of {path}, because the file can no longer be read."
        )
    if not report.rejected:
        return EXIT_OK

    print(f"Rejected: {len(report.rejected)} files.")
    for rejection in report.rejected:
        detail = f" ({rejection.detail})" if rejection.detail else ""
        print(f"  {rejection.source_path}: {rejection.reason}{detail}")
    return EXIT_NOT_ALL


def register(commands: Commands) -> None:
    ingest = commands.add_parser(
        "ingest", help="convert and store a folder of .docx, .pdf, .txt and .md files"
    )
    ingest.add_argument(
        "folder", type=Path, help="the folder to ingest; subfolders are included"
    )
    ingest.set_defaults(handler=_run)
