"""Prices from Yahoo Finance through yfinance, kept in memory with the time each is from.

When the service starts, each symbol's recent daily series is read once, so every price has a
value and a trading day from the start: the day's close once it has ended, its latest price while
it trades. Yahoo's series can miss a day, so a Taiwan series also takes its closes and reference
prices from FinMind and the exchanges' open data (taiwan_sources), and the previous close of every
price follows the series' days (history). Then yfinance's live stream sends each new price.
Outside the regular session it may still send prices, such as US stocks traded overnight; their
change is against the last regular close. A market that sends nothing keeps its daily value, with
its day. A price that cannot be had is missing, never zero.

The stream uses yfinance's synchronous client on a worker thread, as the precedent the plan cites
does. In yfinance 1.8.0 the asynchronous client does not reconnect after a dropped connection,
and after a normal close it loops without awaiting and blocks the service (fixed upstream in
pull request 3048, not yet released). The synchronous client returns from `listen` when the
connection ends, so the stream is opened again after a wait, as that fix does.
"""

import asyncio
import logging
import warnings
from collections.abc import Callable
from dataclasses import dataclass, replace
from datetime import UTC, date, datetime, time
from decimal import Decimal, InvalidOperation
from typing import Any, Protocol

import pandas as pd
import yfinance as yf

from chat_bridge.config import local_data_dir
from chat_bridge.strategy.history import (
    TAIPEI,
    History,
    change_day,
    is_taiwan,
    trading_day,
    zone_of,
)
from chat_bridge.strategy.schemas import Basis
from chat_bridge.strategy.taiwan_sources import (
    SourceError,
    daily_tables,
    finmind_history,
    is_otc,
    notices,
)

logger = logging.getLogger(__name__)

# yfinance logs every end of the stream as an error with its traceback, the close the service
# makes when it stops included, so a person pressing Ctrl+C would see what looks like a crash.
# Its log is not shown; this module logs what the service does when the stream ends or cannot be
# opened, and a symbol whose closes cannot be read.
logging.getLogger("yfinance").addHandler(logging.NullHandler())
logging.getLogger("yfinance").propagate = False
# websockets 17 deprecates connecting without a context manager, as yfinance 1.8.0's synchronous
# client does. The locked websockets still supports it; the notice is for yfinance, not the person.
warnings.filterwarnings(
    "ignore",
    message=r"connect\(\) must be used as a context manager",
    category=DeprecationWarning,
)

# Where the prices come from, as the screen names it.
SOURCE_NAME = "Yahoo Finance"
# Daily closes for about a month, so a long holiday still leaves a previous close.
HISTORY_PERIOD = "1mo"
# yfinance keeps its time zone and cookie caches here instead of the user's own cache folder, so
# what the service writes stays in its local data folder.
CACHE_FOLDER = "yfinance"
# The wait before the stream is opened again, the same as yfinance's own reconnect.
RECONNECT_SECONDS = 3
# How often the subscription is sent again, as yfinance's asynchronous client does.
RESUBSCRIBE_SECONDS = 15


@dataclass(frozen=True)
class Quote:
    symbol: str
    price: Decimal
    # The close before the trading day of this price; none when it is not known.
    previous_close: Decimal | None
    basis: Basis
    # A live price's moment. A daily value's trading day starts at this moment, in the
    # exchange's own time zone, so its date is the day the exchange names.
    at: datetime
    # What the sources gave of the series' recent days, with a daily value; the book keeps it.
    history: History | None = None


class PriceBook:
    """The latest quote of each symbol, and what the sources gave of each series' recent days.

    Every quote of a series takes the previous close of its own trading day from those days when
    they give one, so a live price is measured from the same previous close as the daily value,
    and an ex-dividend day from the reference price.
    """

    def __init__(self) -> None:
        self._quotes: dict[str, Quote] = {}
        self._histories: dict[str, History] = {}

    def get(self, symbol: str) -> Quote | None:
        return self._quotes.get(symbol)

    def put(self, quote: Quote) -> bool:
        """Keep the quote unless the book has a later one, and the days it brings; whether the
        book changed."""
        changed = False
        if quote.history is not None:
            changed = self._learn(quote.symbol, quote.history)
            quote = replace(quote, history=None)
        known = self._quotes.get(quote.symbol)
        if known is not None and quote.at < known.at:
            return changed
        quote = self._with_previous(quote, known)
        if quote == known:
            return changed
        self._quotes[quote.symbol] = quote
        return True

    def needs_days(self, quote: Quote) -> bool:
        """Whether the quote is of a calendar day, where the series trades, after the one its days
        were read on, so reading them again gives a later day. A US price of the same evening is
        measured from the next day (change_day), but a read that evening gives the same day."""
        history = self._histories.get(quote.symbol)
        return (
            history is not None
            and trading_day(quote.symbol, quote.at) > history.read_on
        )

    def _learn(self, symbol: str, history: History) -> bool:
        kept = self._histories.get(symbol)
        self._histories[symbol] = history if kept is None else kept.merged(history)
        known = self._quotes.get(symbol)
        if known is None:
            return False
        updated = self._with_previous(known, None)
        if updated == known:
            return False
        self._quotes[symbol] = updated
        return True

    def _with_previous(self, quote: Quote, known: Quote | None) -> Quote:
        """The quote with the previous close of the day it is measured from (change_day): the
        sources' when they give one; else its own; else, for a live message that does not say it,
        the one known for that day."""
        day = change_day(quote.symbol, quote.at)
        history = self._histories.get(quote.symbol)
        given = None if history is None else history.previous_close(day)
        if given is not None:
            return replace(quote, previous_close=given)
        if (
            quote.previous_close is None
            and known is not None
            and change_day(known.symbol, known.at) == day
        ):
            return replace(quote, previous_close=known.previous_close)
        return quote


def _decimal(value: object, places: int | None = None) -> Decimal | None:
    """A number from yfinance as an exact decimal, from its text; rounded to `places` when
    given. None when it is not a number."""
    if isinstance(value, bool) or not isinstance(value, int | float):
        return None
    try:
        number = Decimal(str(value))
    except InvalidOperation:
        return None
    if not number.is_finite():
        return None
    return number if places is None else number.quantize(Decimal(1).scaleb(-places))


def quote_from_message(message: dict[str, Any]) -> Quote | None:
    """A quote from one message of the live stream; none when it lacks a symbol, a price, a time
    or the number of decimals to show.

    The stream sends the price as a binary float with `price_hint`, the decimals to show, and
    `change`, the change since the previous close.
    """
    symbol = message.get("id")
    if not isinstance(symbol, str) or not symbol:
        return None
    try:
        # 64-bit integers arrive as text, as protobuf's JSON mapping writes them.
        millis = int(message["time"])
        places = int(message["price_hint"])
    except (KeyError, TypeError, ValueError):
        return None
    if places < 0:
        return None
    price = _decimal(message.get("price"), places)
    if price is None:
        return None
    change = _decimal(message.get("change"), places)
    return Quote(
        symbol=symbol,
        price=price,
        previous_close=None if change is None else price - change,
        basis="live",
        at=datetime.fromtimestamp(millis / 1000, UTC),
    )


def history_from_frame(symbol: str, frame: pd.DataFrame, read_on: date) -> History:
    """The days of a Yahoo daily series: each day's close, and the days it lists without one.

    The latest is the day's close once that day has ended, and its latest price while it trades.
    """
    if "Close" not in frame:
        return History(read_on=read_on)
    closes: dict[date, Decimal] = {}
    missing: set[date] = set()
    for moment, value in frame["Close"].items():
        day = trading_day(symbol, pd.Timestamp(moment).to_pydatetime())
        close = None if pd.isna(value) else _decimal(float(value))
        if close is None:
            missing.add(day)
        else:
            closes[day] = close
    return History(
        read_on=read_on, closes=closes, missing=frozenset(missing - closes.keys())
    )


def latest_quote(symbol: str, history: History) -> Quote | None:
    """The series' latest daily value with the previous close of its day, and its days."""
    day = history.latest
    if day is None:
        return None
    return Quote(
        symbol=symbol,
        price=history.closes[day],
        previous_close=history.previous_close(day),
        basis="daily",
        at=datetime.combine(day, time(), zone_of(symbol)),
        history=history,
    )


def _read_yahoo_history(symbol: str) -> History | None:
    # Not adjusted for dividends, so the closes are the prices traded on those days. The days
    # Yahoo has no close for are kept (yfinance drops them by default), so a missing day is seen
    # as missing instead of the day before it standing in.
    read_on = datetime.now(zone_of(symbol)).date()
    try:
        frame = yf.Ticker(symbol).history(
            period=HISTORY_PERIOD,
            interval="1d",
            auto_adjust=False,
            rounding=True,
            keepna=True,
        )
    except Exception as error:
        # yfinance raises its own errors and its HTTP client's; whatever the cause, this
        # symbol's Yahoo series is missing and the other sources go on.
        logger.warning("No recent closes for %s: %s", symbol, error)
        return None
    history = history_from_frame(symbol, frame, read_on)
    if history.latest is None:
        # yfinance answers some failures with an empty series instead of an error.
        logger.warning("No recent closes for %s.", symbol)
    return history


def _yahoo_previous_close(symbol: str) -> Decimal | None:
    """Yahoo's own quote of the previous close: the regular session's when it gives one, which is
    the close (NVDA 165.05 against 165.2596); else its other one (0050 and 006208 gave only that,
    and it was the exchange's close)."""
    try:
        info = yf.Ticker(symbol).fast_info
        values = [info.regular_market_previous_close, info.previous_close]
    except Exception as error:
        logger.warning("Yahoo's quote of %s could not be read: %s", symbol, error)
        return None
    places = 2 if is_taiwan(symbol) else 4
    return next(
        (number for value in values if (number := _decimal(value, places)) is not None),
        None,
    )


def _merge(kept: History | None, added: History) -> History:
    return added if kept is None else kept.merged(added)


def _knows(history: History | None, days: list[date]) -> bool:
    return history is not None and all(
        history.previous_close(day) is not None for day in days
    )


async def add_taiwan_sources(
    symbols: list[str],
    histories: dict[str, History],
    today: date,
    changed: Callable[[str], None],
) -> None:
    """Add to the Taiwan series' days FinMind's closes and reference prices, the announced
    ex-dividend days, and, for a series still without the previous close of its latest day or of
    `today` (in Taipei), its market's open-data table (spec 012 FR-002, FR-003).

    `changed` is told each series whose days grew, as each source answers, so its price is shown
    without waiting for the sources after it. Once FinMind fails it is not asked for the other
    series in this read: each request would wait as long, and the tables still follow.
    """
    taiwan = [symbol for symbol in symbols if is_taiwan(symbol)]
    if not taiwan:
        return

    def add(symbol: str, history: History) -> None:
        histories[symbol] = _merge(histories.get(symbol), history)
        changed(symbol)

    for symbol in taiwan:
        try:
            add(symbol, await asyncio.to_thread(finmind_history, symbol, today))
        except SourceError as error:
            logger.warning("FinMind is not read for the other series: %s", error)
            break
    try:
        announced = await asyncio.to_thread(notices, taiwan, today)
    except SourceError as error:
        logger.warning("The ex-dividend notices could not be read: %s", error)
        announced = {}
    for symbol, days in announced.items():
        add(symbol, History(read_on=today, dividends=days))

    def days_of(symbol: str) -> list[date]:
        latest = histories[symbol].latest if symbol in histories else None
        return [today] if latest is None else [latest, today]

    lacking = [
        symbol
        for symbol in taiwan
        if not _knows(histories.get(symbol), days_of(symbol))
        # The OTC market gives the reference price of its next day; an ex-dividend day today
        # takes it instead of one worked out from the notice.
        or (
            is_otc(symbol)
            and today in announced.get(symbol, {})
            and today not in histories[symbol].given
        )
    ]
    if not lacking:
        return
    try:
        tables = await asyncio.to_thread(daily_tables, lacking, today, announced)
    except SourceError as error:
        logger.warning("The exchanges' daily tables could not be read: %s", error)
        return
    for symbol, history in tables.items():
        add(symbol, history)


async def add_yahoo_quotes(
    symbols: list[str],
    histories: dict[str, History],
    changed: Callable[[str], None],
) -> None:
    """Add Yahoo's own quote of the previous close to each series whose latest day has none from
    its other sources, and tell `changed`."""
    for symbol in symbols:
        history = histories.get(symbol)
        latest = None if history is None else history.latest
        if (
            history is None
            or latest is None
            or history.previous_close(latest) is not None
        ):
            continue
        previous = await asyncio.to_thread(_yahoo_previous_close, symbol)
        if previous is not None:
            histories[symbol] = history.merged(
                History(read_on=history.read_on, given={latest: previous})
            )
            changed(symbol)


class PriceSource(Protocol):
    """Where prices come from: Yahoo in the service, a stand-in in tests."""

    async def read_closes(
        self, symbols: list[str], on_quote: Callable[[Quote], None]
    ) -> None:
        """Send each symbol's latest daily value to `on_quote`."""
        ...

    async def stream(
        self,
        symbols: list[str],
        on_quote: Callable[[Quote], None],
        on_open: Callable[[bool], None],
    ) -> None:
        """Send each new price of the symbols to `on_quote` until cancelled, and tell `on_open`
        each time the live connection opens or ends."""
        ...


class YahooPrices:
    """Recent daily closes, then the live stream, from Yahoo Finance."""

    def __init__(self) -> None:
        # Stream messages without a symbol, price, time or decimals: dropped and counted.
        self.dropped = 0
        yf.set_tz_cache_location(str(local_data_dir() / CACHE_FOLDER))

    async def read_closes(
        self, symbols: list[str], on_quote: Callable[[Quote], None]
    ) -> None:
        """Each symbol's latest daily value with the previous close of its day, sent as soon as
        Yahoo's series gives it and again each time a later source adds to its days. The sources
        come in the order spec 012 gives: Yahoo's series; for Taiwan, FinMind, the notices and
        the exchanges' tables; then Yahoo's own quote. The other markets' series take Yahoo's
        quote before the Taiwan sources are read, so a slow Taiwan source holds none of them."""
        histories: dict[str, History] = {}

        def show(symbol: str) -> None:
            quote = latest_quote(symbol, histories[symbol])
            if quote is not None:
                on_quote(quote)

        # One symbol at a time: yfinance's cache database is locked when several threads first
        # use it at once, and the symbol that loses gets no price.
        for symbol in symbols:
            history = await asyncio.to_thread(_read_yahoo_history, symbol)
            if history is not None:
                histories[symbol] = history
                show(symbol)
        taiwan = [symbol for symbol in symbols if is_taiwan(symbol)]
        others = [symbol for symbol in symbols if not is_taiwan(symbol)]
        await add_yahoo_quotes(others, histories, show)
        await add_taiwan_sources(taiwan, histories, datetime.now(TAIPEI).date(), show)
        await add_yahoo_quotes(taiwan, histories, show)

    async def stream(
        self,
        symbols: list[str],
        on_quote: Callable[[Quote], None],
        on_open: Callable[[bool], None],
    ) -> None:
        try:
            await self._stream(symbols, on_quote, on_open)
        finally:
            if self.dropped:
                logger.info(
                    "Dropped %d price messages that lacked a field.", self.dropped
                )

    def _on_message(
        self, message: dict[str, Any], on_quote: Callable[[Quote], None]
    ) -> None:
        quote = quote_from_message(message)
        if quote is None:
            self.dropped += 1
            return
        on_quote(quote)

    async def _stream(
        self,
        symbols: list[str],
        on_quote: Callable[[Quote], None],
        on_open: Callable[[bool], None],
    ) -> None:
        loop = asyncio.get_running_loop()

        def handle(message: dict[str, Any]) -> None:
            # Called on the stream's thread; the quote is handled on the service's loop.
            loop.call_soon_threadsafe(self._on_message, message, on_quote)

        # Whether the last attempt failed. Without a network the stream is tried every few
        # seconds for as long as the service runs; the failure is said once, and again only
        # after the stream has opened in between, so the terminal is not filled with it.
        failing = False
        while True:
            stream = yf.WebSocket(verbose=False)
            resubscribing: asyncio.Task[None] | None = None
            try:
                await asyncio.to_thread(stream.subscribe, symbols)
                if failing:
                    logger.info("The live price stream is open again.")
                failing = False
                on_open(True)
                resubscribing = asyncio.create_task(_resubscribe(stream, symbols))
                await asyncio.to_thread(stream.listen, handle)
                logger.info(
                    "The live price stream ended; it is opened again in %d seconds.",
                    RECONNECT_SECONDS,
                )
            except Exception as error:
                # Opening the connection raises the network's errors; the stream is tried again.
                if not failing:
                    logger.warning(
                        "The live price stream could not be opened: %s. It is tried again "
                        "every %d seconds; prices stay as they are until it opens.",
                        error,
                        RECONNECT_SECONDS,
                    )
                failing = True
            finally:
                on_open(False)
                if resubscribing is not None:
                    resubscribing.cancel()
                # Closing ends `listen` on its thread, which would otherwise keep waiting for a
                # message after the service stops.
                await asyncio.to_thread(stream.close)
            await asyncio.sleep(RECONNECT_SECONDS)


async def _resubscribe(stream: yf.WebSocket, symbols: list[str]) -> None:
    """Send the subscription again every so often while the stream is open.

    Yahoo stops sending prices for a subscription that is not renewed, and the connection stays
    open, so nothing would show that prices stopped. yfinance's asynchronous client renews every
    15 seconds; its synchronous one does not, so it is done here with its own `subscribe`, which
    sends the whole subscription again. The connection allows a send while another thread waits
    in `recv`.
    """
    while True:
        await asyncio.sleep(RESUBSCRIBE_SECONDS)
        try:
            await asyncio.to_thread(stream.subscribe, symbols)
        except Exception as error:
            # The connection ended; `listen` returns on its own and the stream is opened again.
            logger.debug("Renewing the price subscription failed: %s", error)
            return
