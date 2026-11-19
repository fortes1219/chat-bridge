"""Turn one file into Markdown text. The reader is picked by file extension, as in private-gpt."""

import codecs
import functools
from collections.abc import Callable
from enum import StrEnum
from pathlib import Path

from markitdown import MarkItDown, MarkItDownException

# private-gpt checks the first 8 KB of a text file for NUL bytes to catch binary files.
BINARY_PROBE_BYTES = 8192


class RejectReason(StrEnum):
    UNSUPPORTED_TYPE = "unsupported file type"
    NO_TEXT = "no text to extract (empty file, or a scan without a text layer)"
    NOT_UTF8 = "text file is not UTF-8"
    BINARY = "binary content in a text file"
    CONVERSION_FAILED = "conversion to Markdown failed"
    INVALID_FRONT_MATTER = "invalid front matter"


class UnreadableFileError(Exception):
    """A supported file that yields no usable text. The batch goes on without it."""

    def __init__(self, reason: RejectReason, detail: str = "") -> None:
        super().__init__(f"{reason}: {detail}" if detail else str(reason))
        self.reason = reason
        self.detail = detail


def _read_text(path: Path) -> str:
    # Unlike private-gpt, there is no fallback to Latin-1 or cp1252: for Chinese text that
    # fallback "succeeds" with garbled characters, so a non-UTF-8 file is refused instead.
    data = path.read_bytes()
    if data.startswith((codecs.BOM_UTF16_LE, codecs.BOM_UTF16_BE)):
        encoding = "utf-16"
    elif b"\x00" in data[:BINARY_PROBE_BYTES]:
        raise UnreadableFileError(RejectReason.BINARY)
    else:
        encoding = "utf-8-sig"
    try:
        return data.decode(encoding)
    except UnicodeDecodeError as error:
        raise UnreadableFileError(RejectReason.NOT_UTF8, str(error)) from error


@functools.cache
def _markitdown() -> MarkItDown:
    return MarkItDown(enable_plugins=False)


def _convert_with_markitdown(path: Path) -> str:
    try:
        result = _markitdown().convert(path)
    except MarkItDownException as error:
        first_line = (
            str(error).strip().splitlines()[0]
            if str(error).strip()
            else type(error).__name__
        )
        raise UnreadableFileError(RejectReason.CONVERSION_FAILED, first_line) from error
    markdown: str = result.markdown
    return markdown


Reader = Callable[[Path], str]

READERS: dict[str, Reader] = {
    ".md": _read_text,
    ".txt": _read_text,
    ".docx": _convert_with_markitdown,
    ".pdf": _convert_with_markitdown,
}


def is_supported(path: Path) -> bool:
    return path.suffix.lower() in READERS


def read_markdown(path: Path) -> str:
    """Return the file as Markdown text, or raise UnreadableFileError. No OCR is done."""
    reader = READERS.get(path.suffix.lower())
    if reader is None:
        raise UnreadableFileError(
            RejectReason.UNSUPPORTED_TYPE, path.suffix or "(no extension)"
        )
    text = reader(path)
    if not text.strip():
        raise UnreadableFileError(RejectReason.NO_TEXT)
    return text
