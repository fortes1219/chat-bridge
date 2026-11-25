"""Prices from Yahoo Finance through yfinance, kept in memory with the time each is from.

When the service starts, each symbol's recent daily series is read once, so every price has a
value and a trading day from the start: the day's close once it has ended, its latest price while
it trades. Then yfinance's live stream sends each new price. Outside the regular session it may
still send prices, such as US stocks traded overnight; their change is against the last regular
close. A market that sends nothing keeps its daily value, with its day. A price that cannot be had
is missing, never zero.

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
from datetime import UTC, datetime
from decimal import Decimal, InvalidOperation
from typing import Any, Protocol

import pandas as pd
import yfinance as yf

from chat_bridge.config import local_data_dir
from chat_bridge.strategy.schemas import Basis

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


class PriceBook:
    """The latest quote of each symbol."""

    def __init__(self) -> None:
        self._quotes: dict[str, Quote] = {}

    def get(self, symbol: str) -> Quote | None:
        return self._quotes.get(symbol)

    def put(self, quote: Quote) -> bool:
        """Keep the quote unless the book has a later one; whether the book changed.

        A live message that does not say the previous close keeps the one already known.
        """
        known = self._quotes.get(quote.symbol)
        if known is not None:
            if quote.at < known.at:
                return False
            if quote.previous_close is None:
                quote = replace(quote, previous_close=known.previous_close)
            if quote == known:
                return False
        self._quotes[quote.symbol] = quote
        return True


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


def quote_from_history(symbol: str, frame: pd.DataFrame) -> Quote | None:
    """The latest daily value and the close of the trading day before it; none when the series
    has no close.

    The latest is the day's close once that day has ended, and its latest price while it trades.
    The series keeps the days Yahoo has no close for. When the day before the latest is one of
    them, the previous close is not known and is none: the close of an earlier day would make a
    two-day move look like one day's.
    """
    if "Close" not in frame:
        return None
    closes = frame["Close"]
    known = [position for position, close in enumerate(closes) if pd.notna(close)]
    if not known:
        return None
    latest = known[-1]
    price = _decimal(float(closes.iloc[latest]))
    if price is None:
        return None
    before = closes.iloc[latest - 1] if latest > 0 else None
    previous = None if before is None or pd.isna(before) else _decimal(float(before))
    day: pd.Timestamp = closes.index[latest]
    return Quote(
        symbol=symbol,
        price=price,
        previous_close=previous,
        basis="daily",
        at=day.to_pydatetime(),
    )


def _read_recent_closes(symbol: str) -> Quote | None:
    # Not adjusted for dividends, so the closes are the prices traded on those days. The days
    # Yahoo has no close for are kept (yfinance drops them by default), so a missing day is seen
    # as missing instead of the day before it standing in.
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
        # symbol's price is missing and the others go on.
        logger.warning("No recent closes for %s: %s", symbol, error)
        return None
    quote = quote_from_history(symbol, frame)
    if quote is None:
        # yfinance answers some failures with an empty series instead of an error.
        logger.warning("No recent closes for %s.", symbol)
    return quote


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
        # One symbol at a time: yfinance's cache database is locked when several threads first
        # use it at once, and the symbol that loses gets no price.
        for symbol in symbols:
            quote = await asyncio.to_thread(_read_recent_closes, symbol)
            if quote is not None:
                on_quote(quote)

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
