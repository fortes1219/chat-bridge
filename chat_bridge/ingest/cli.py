"""The `chat-bridge ingest <folder>` subcommand."""

import argparse
import asyncio
from pathlib import Path

from chat_bridge.cli import EXIT_NOT_ALL, EXIT_OK, Commands, print_error
from chat_bridge.errors import LocalSetupError
from chat_bridge.ingest import service as ingest_service
from chat_bridge.ingest.service import IndexUpdate

INDEX_NOTES = {
    IndexUpdate.WRITTEN_FILES: "entries added for the written files",
    IndexUpdate.KEYWORDS: "keywords rebuilt for every section, embeddings kept",
    IndexUpdate.ALL: "every section rebuilt and embedded again",
}


def _run(args: argparse.Namespace) -> int:
    folder: Path = args.folder
    if not folder.is_dir():
        return print_error(f"not a folder: {folder}")
    try:
        report = asyncio.run(
            ingest_service.ingest_folder(folder.resolve(), replace=args.replace)
        )
    except LocalSetupError as error:
        return print_error(str(error))

    if report.replace_refused:
        _print_rejections(report)
        return print_error(
            f"no file in {folder} could be read, so nothing was replaced; "
            "the knowledge base is as it was"
        )
    print(f"Written: {len(report.written)} files, {report.sections_written} sections.")
    print(f"Unchanged and skipped: {len(report.unchanged)} files.")
    if report.index_update != IndexUpdate.NONE:
        print(f"Search index: {INDEX_NOTES[report.index_update]}.")
    for path in report.removed:
        print(
            f"Removed the stored version of {path}, because the file can no longer be read."
        )
    if report.not_in_folder:
        print(
            f"Removed {len(report.not_in_folder)} documents that are not in {folder}:"
        )
        for path in report.not_in_folder:
            print(f"  {path}")
    if report.others_kept:
        print(
            f"The knowledge base also holds {report.others_kept} documents that are not in "
            f"{folder}; they are answered from too. Run with --replace to keep only this "
            "folder's documents."
        )
    if not report.rejected:
        return EXIT_OK
    _print_rejections(report)
    return EXIT_NOT_ALL


def _print_rejections(report: ingest_service.IngestReport) -> None:
    if not report.rejected:
        return
    print(f"Rejected: {len(report.rejected)} files.")
    for rejection in report.rejected:
        detail = f" ({rejection.detail})" if rejection.detail else ""
        print(f"  {rejection.source_path}: {rejection.reason}{detail}")


def register(commands: Commands) -> None:
    ingest = commands.add_parser(
        "ingest",
        help="convert and store a folder of .docx, .doc, .pdf, .txt and .md files",
    )
    ingest.add_argument(
        "folder", type=Path, help="the folder to ingest; subfolders are included"
    )
    ingest.add_argument(
        "--replace",
        action="store_true",
        help="keep only this folder's documents: remove every stored document that is not "
        "in it, the sample news included",
    )
    ingest.set_defaults(handler=_run)
