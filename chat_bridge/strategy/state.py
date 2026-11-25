"""The strategy the page sees, kept in memory between writes, and the prices that move it.

The holdings, targets and open proposal are read from the database once, and again only after
something writes them. A new price updates the price book and recomputes the view in memory: it
reads nothing from the database, so its cost follows the number of holdings, not the number of
quotes.

There is one per process, as there is one service and one page's strategy: the endpoints, the
chat's revision answers and the real-time connection all read and write the same one.
"""

import asyncio
import logging
import time
from collections.abc import Awaitable, Callable

from chat_bridge.strategy import store
from chat_bridge.strategy.compute import priced_symbols, valuation
from chat_bridge.strategy.prices import PriceBook, PriceSource, Quote
from chat_bridge.strategy.schemas import HoldingView, StoredStrategy, StrategyView

logger = logging.getLogger(__name__)

Listener = Callable[[StrategyView], Awaitable[None]]
# How long the service waits for the recent closes before it takes requests. Past it, the service
# starts anyway, as Yahoo may be slow or out of reach.
CLOSES_WAIT_SECONDS = 20


class StrategyState:
    def __init__(self) -> None:
        self.book = PriceBook()
        self._live = False
        self._stored: StoredStrategy | None = None
        # How many writes there have been, so a read that a write overtook is not kept.
        self._writes = 0
        self._reading = asyncio.Lock()
        self._listeners: list[Listener] = []
        self._feed: asyncio.Task[None] | None = None
        # The price source and the series the live stream follows, so a change of holdings can
        # restart it on the new ones.
        self._source: PriceSource | None = None
        self._symbols: list[str] = []
        self._following: asyncio.Task[None] | None = None
        # Publishing tasks, kept so they are not collected while they run.
        self._publishing: set[asyncio.Task[None]] = set()

    async def view(self) -> StrategyView:
        """The strategy with its prices. Raises store.ProfileMissingError."""
        stored = await self._read()
        return StrategyView(
            **stored.model_dump(),
            valuation=valuation(stored.holdings, self.book, live=self._live),
        )

    async def _read(self) -> StoredStrategy:
        async with self._reading:
            if self._stored is not None:
                return self._stored
            written = self._writes
            stored = await store.read_strategy()
            # A write while this read ran may have made it out of date: it is used for this
            # view and read again next time.
            if written == self._writes:
                self._stored = stored
            return stored

    def written(self, stored: StoredStrategy | None = None) -> None:
        """After a write: keep the strategy the write returned, or read it again on next use.

        Nothing is sent: the page that wrote updates itself from the response, and the next
        price sends the strategy as written.
        """
        self._writes += 1
        self._stored = stored

    def live(self, is_open: bool) -> None:
        """The live price stream opened or ended: the page says whether prices are following."""
        if is_open != self._live:
            self._live = is_open
            self._publish()

    def price(self, quote: Quote) -> None:
        """A new price: recompute and send the view when it changed anything."""
        if self.book.put(quote):
            self._publish()

    def _publish(self) -> None:
        if not self._listeners:
            return
        task = asyncio.get_running_loop().create_task(self._send())
        self._publishing.add(task)
        task.add_done_callback(self._publishing.discard)

    async def _send(self) -> None:
        try:
            view = await self.view()
        except store.ProfileMissingError:
            return
        for listener in self._listeners:
            await listener(view)

    async def start(
        self, source: PriceSource | None, listeners: list[Listener]
    ) -> None:
        """Begin with an empty price book and read the profile again; read the recent closes and
        start the live stream, sending the view to `listeners` after each price that changes it.

        The closes are read before this returns, for at most CLOSES_WAIT_SECONDS, so the first page
        that opens shows prices instead of every holding left out.
        """
        self.book = PriceBook()
        self._live = False
        self._stored = None
        # Made on the service's own loop, which a lock binds to when it is first waited on.
        self._reading = asyncio.Lock()
        self._listeners = list(listeners)
        self._source = source
        self._symbols = []
        if source is None:
            return
        try:
            stored = await self._read()
        except store.ProfileMissingError:
            logger.warning("There is no profile, so no prices are read.")
            return
        symbols = priced_symbols(stored.holdings)
        # Said, so the pause before the page opens has a reason on the screen.
        logger.info("Reading the recent prices of %d series.", len(symbols))
        began = time.perf_counter()
        try:
            await asyncio.wait_for(
                source.read_closes(symbols, self.price), CLOSES_WAIT_SECONDS
            )
        except TimeoutError:
            logger.warning(
                "The recent prices were not all read within %d seconds; the service starts "
                "without the rest.",
                CLOSES_WAIT_SECONDS,
            )
        found = sum(self.book.get(symbol) is not None for symbol in symbols)
        logger.info(
            "Read %d of %d recent prices in %.1f seconds.",
            found,
            len(symbols),
            time.perf_counter() - began,
        )
        self._symbols = symbols
        self._feed = asyncio.get_running_loop().create_task(
            self._run_stream(source, symbols)
        )

    def follow(self, holdings: list[HoldingView]) -> None:
        """After the holdings changed: read the recent closes of the series with no price yet, the
        new holdings' among them, and restart the live stream on the saved holdings, in the
        background. Each price reaches the page as it comes, so saving does not wait for Yahoo.
        Holdings saved with the same series leave the feed as it is."""
        symbols = priced_symbols(holdings)
        if self._source is None or symbols == self._symbols:
            return
        previous = self._following
        self._following = asyncio.get_running_loop().create_task(
            self._follow(self._source, symbols, previous)
        )

    async def _follow(
        self,
        source: PriceSource,
        symbols: list[str],
        previous: asyncio.Task[None] | None,
    ) -> None:
        # A save that came before this one finishes first, so the last save's holdings win.
        if previous is not None:
            await asyncio.gather(previous, return_exceptions=True)
        await self._stop_feed()
        new = [symbol for symbol in symbols if self.book.get(symbol) is None]
        if new:
            try:
                await asyncio.wait_for(
                    source.read_closes(new, self.price), CLOSES_WAIT_SECONDS
                )
            except TimeoutError:
                logger.warning(
                    "The recent prices of %s were not read within %d seconds.",
                    ", ".join(new),
                    CLOSES_WAIT_SECONDS,
                )
            except Exception:
                # A background task's error reaches no one: it is logged, and the live stream
                # still starts on the saved holdings, so their prices can come from it.
                logger.exception(
                    "The recent prices of %s could not be read.", ", ".join(new)
                )
        self._symbols = symbols
        self._feed = asyncio.get_running_loop().create_task(
            self._run_stream(source, symbols)
        )

    async def stop(self) -> None:
        """Stop the price feed and wait for it to close its connection."""
        self._listeners = []
        following, self._following = self._following, None
        if following is not None:
            following.cancel()
            await asyncio.gather(following, return_exceptions=True)
        await self._stop_feed()

    async def _stop_feed(self) -> None:
        feed, self._feed = self._feed, None
        if feed is None:
            return
        feed.cancel()
        try:
            await feed
        except asyncio.CancelledError:
            pass

    async def _run_stream(self, source: PriceSource, symbols: list[str]) -> None:
        try:
            await source.stream(symbols, self.price, self.live)
        except Exception:
            # A background task's error reaches no one; it is logged, and the screen keeps the
            # prices it has, each with its time.
            logger.exception("The price feed stopped.")


STATE = StrategyState()
