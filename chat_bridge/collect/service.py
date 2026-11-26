"""The market moves of news files: each file's section from one read of the daily closes."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from pathlib import Path

from chat_bridge.collect import news_files
from chat_bridge.collect.closes import Closes, read_closes
from chat_bridge.collect.markets import MarketSeries, market_series
from chat_bridge.collect.moves import section
from chat_bridge.collect.news_files import NewsFile, NewsFileError
from chat_bridge.collect.pages import Kind

# Days read before the earliest and after the latest event, so day −2 and day +5 are in the span
# across a long holiday.
SPAN_DAYS = 21


@dataclass(frozen=True)
class FileOutcome:
    path: Path
    kind: Kind
    detail: str = ""


def news_paths(targets: list[Path]) -> list[Path]:
    """The Markdown files given, and those in the folders given, in order."""
    found: list[Path] = []
    for target in targets:
        found += sorted(target.rglob("*.md")) if target.is_dir() else [target]
    return list(dict.fromkeys(found))


def collect_market_moves(
    paths: list[Path],
    *,
    now: datetime | None = None,
    listed: MarketSeries | None = None,
    closes: Closes | None = None,
) -> list[FileOutcome]:
    """Write each news file's section of market moves. `closes` stands in for reading them.
    Raises MarketSeriesFileError and ClosesError; when the closes cannot be read, no file is
    changed."""
    moment = (now or datetime.now(UTC)).replace(microsecond=0)
    series = listed or market_series()
    outcomes: list[FileOutcome] = []
    readable: list[NewsFile] = []
    for path in paths:
        try:
            readable.append(news_files.read(path, series))
        except (NewsFileError, OSError, UnicodeDecodeError) as error:
            outcomes.append(FileOutcome(path, "refused", str(error)))
    if not readable:
        return outcomes
    dates = [news.event.event_date for news in readable]
    start = min(dates) - timedelta(days=SPAN_DAYS)
    end = min(max(dates) + timedelta(days=SPAN_DAYS), moment.date())
    found = (
        closes if closes is not None else read_closes(series.series, start, end, moment)
    )
    symbols = [one.symbol for one in series.series]
    for news in readable:
        computed = section(news.event, series, found)
        try:
            text = news_files.with_section(news, computed, moment, symbols)
        except NewsFileError as error:
            outcomes.append(FileOutcome(news.path, "refused", str(error)))
            continue
        if text is None:
            outcomes.append(FileOutcome(news.path, "unchanged"))
            continue
        news.path.write_text(text, encoding="utf-8", newline="\n")
        outcomes.append(FileOutcome(news.path, "written"))
    return outcomes
