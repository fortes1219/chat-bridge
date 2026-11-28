"""What was read of each series, kept for a day: one file a series under local_data/price_history.

A market's series are read together and saved with the same read time, so the trading days of a
market always come from one read. A stored read serves a lookup while it is less than a day old
and starts early enough; a close published later the same day shows once it has expired. The
store only saves reads: a read that cannot be kept is still used, as yfinance still answers when
its own cache cannot be made, and the next question reads again.
"""

from __future__ import annotations

import os
import threading
from dataclasses import dataclass
from datetime import date, datetime, timedelta
from pathlib import Path

from pydantic import BaseModel, ConfigDict, ValidationError

from chat_bridge.config import local_data_dir
from chat_bridge.price_history.closes import SeriesCloses

KEPT_FOR = timedelta(days=1)
FOLDER = "price_history"


class _Stored(BaseModel):
    model_config = ConfigDict(extra="forbid")

    symbol: str
    start: date
    read_at: datetime
    closes: dict[date, float]
    filled: list[date]
    dividends: list[date]


@dataclass(frozen=True)
class Stored:
    start: date
    read_at: datetime
    closes: SeriesCloses


def folder() -> Path:
    return local_data_dir() / FOLDER


def _path(symbol: str, under: Path) -> Path:
    # "^" begins an index symbol; it stays out of file names.
    return under / f"{symbol.replace('^', '_')}.json"


def load(symbol: str, under: Path | None = None) -> Stored | None:
    """The stored read of a symbol, or None when there is none or it cannot be read."""
    path = _path(symbol, under or folder())
    try:
        stored = _Stored.model_validate_json(path.read_text(encoding="utf-8"))
    except (OSError, ValidationError):
        return None
    if stored.symbol != symbol:
        return None
    closes = SeriesCloses(
        dict(stored.closes), set(stored.filled), set(stored.dividends)
    )
    return Stored(stored.start, stored.read_at, closes)


def serves(stored: Stored | None, start: date, now: datetime) -> bool:
    """Whether a stored read serves a lookup from `start`: it is less than a day old and starts
    on or before that day."""
    return (
        stored is not None and now - stored.read_at < KEPT_FOR and stored.start <= start
    )


def save(
    symbol: str,
    start: date,
    read_at: datetime,
    closes: SeriesCloses,
    under: Path | None = None,
) -> None:
    """Keep a read. Written to a new file and moved into place, so a read never finds half a
    file. Raises OSError when it cannot be kept: on Windows a file another question has open
    cannot be replaced, and a disk can be full."""
    target = _path(symbol, under or folder())
    target.parent.mkdir(parents=True, exist_ok=True)
    stored = _Stored(
        symbol=symbol,
        start=start,
        read_at=read_at,
        closes=closes.closes,
        filled=sorted(closes.filled),
        dividends=sorted(closes.dividends),
    )
    staged = target.with_name(
        f"{target.name}.{os.getpid()}-{threading.get_ident()}.part"
    )
    try:
        staged.write_text(stored.model_dump_json(), encoding="utf-8")
        os.replace(staged, target)
    except OSError:
        # Nothing half-written is left behind for the folder to fill up with.
        staged.unlink(missing_ok=True)
        raise
