"""Read one file. The reader is picked by file extension, as in private-gpt.

Each format is read by a package: markitdown for `.docx`, office-oxide for Word 97 `.doc`, and
pypdf for PDF. None of them needs a program installed beside Python. No OCR is done.

Word and text files become Markdown. A PDF becomes its pages: its text layer is plain text,
not Markdown, and has no headings to cut it by.
"""

import codecs
import functools
from collections.abc import Callable
from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path

import office_oxide
from markitdown import MarkItDown, MarkItDownException
from pypdf import PdfReader
from pypdf.errors import PyPdfError

# private-gpt checks the first 8 KB of a text file for NUL bytes to catch binary files.
BINARY_PROBE_BYTES = 8192


class RejectReason(StrEnum):
    UNSUPPORTED_TYPE = "unsupported file type"
    NO_TEXT = "no text to extract (empty file, or a scan without a text layer)"
    NOT_UTF8 = "text file is not UTF-8"
    BINARY = "binary content in a text file"
    CONVERSION_FAILED = "conversion to Markdown failed"
    INVALID_FRONT_MATTER = "invalid front matter"
    OPENDOCUMENT = "OpenDocument text is not read; save it as .docx or PDF"


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
        raise UnreadableFileError(
            RejectReason.CONVERSION_FAILED, _first_line(error)
        ) from error
    markdown: str = result.markdown
    return markdown


def _first_line(error: Exception) -> str:
    text = str(error).strip()
    return text.splitlines()[0] if text else type(error).__name__


@dataclass(frozen=True)
class Page:
    """One page of a PDF: its label as the document numbers it, and its text."""

    label: str
    text: str


def _read_pdf_pages(path: Path) -> list[Page]:
    # Each page keeps its own label (roman numerals in a preface, for example), because that is
    # what a reader finds it by in the original. A page without text, such as a scan, is left out.
    try:
        reader = PdfReader(path)
        labels = reader.page_labels
        pages = [
            Page(labels[index], (page.extract_text() or "").strip())
            for index, page in enumerate(reader.pages)
        ]
    except (PyPdfError, OSError) as error:
        raise UnreadableFileError(
            RejectReason.CONVERSION_FAILED, _first_line(error)
        ) from error
    return [page for page in pages if page.text]


def _convert_word_97(path: Path) -> str:
    try:
        markdown: str = office_oxide.to_markdown(str(path))
    except office_oxide.OfficeOxideError as error:
        raise UnreadableFileError(
            RejectReason.CONVERSION_FAILED, _first_line(error)
        ) from error
    return markdown


Reader = Callable[[Path], str]
PageReader = Callable[[Path], list[Page]]

READERS: dict[str, Reader] = {
    ".md": _read_text,
    ".txt": _read_text,
    ".docx": _convert_with_markitdown,
    ".doc": _convert_word_97,
}
PAGE_READERS: dict[str, PageReader] = {".pdf": _read_pdf_pages}
# Types that are recognised but not read, each with what the person can do instead. This demo
# does not read OpenDocument text: the maintainer decided so, and the report says how to convert.
REFUSED_TYPES: dict[str, RejectReason] = {".odt": RejectReason.OPENDOCUMENT}


def is_supported(path: Path) -> bool:
    return path.suffix.lower() in READERS or is_paged(path)


def is_paged(path: Path) -> bool:
    """Whether the file is read as pages rather than as Markdown."""
    return path.suffix.lower() in PAGE_READERS


def read_pages(path: Path) -> list[Page]:
    """Return the pages that have text, or raise UnreadableFileError. No OCR is done."""
    pages = PAGE_READERS[path.suffix.lower()](path)
    if not pages:
        raise UnreadableFileError(RejectReason.NO_TEXT)
    return pages


def unsupported_reason(path: Path) -> RejectReason:
    """Why a file that has no reader is not read."""
    return REFUSED_TYPES.get(path.suffix.lower(), RejectReason.UNSUPPORTED_TYPE)


def read_markdown(path: Path) -> str:
    """Return the file as Markdown text, or raise UnreadableFileError. No OCR is done."""
    reader = READERS.get(path.suffix.lower())
    if reader is None:
        raise UnreadableFileError(
            unsupported_reason(path), path.suffix or "(no extension)"
        )
    text = reader(path)
    if not text.strip():
        raise UnreadableFileError(RejectReason.NO_TEXT)
    return text
