"""The strategy in memory: read once, recomputed for each price, sent to the open pages.

The store is stubbed and counts its reads; the price feed is a stand-in.
"""

import asyncio
import time
from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal

import pytest

from chat_bridge.strategy import state as state_module
from chat_bridge.strategy import store
from chat_bridge.strategy.prices import Quote
from chat_bridge.strategy.schemas import (
    HoldingView,
    RuleChecks,
    StoredStrategy,
    StrategyView,
    TargetRow,
)
from chat_bridge.strategy.state import StrategyState
from tests.strategy.test_valuation import HOLDINGS

STORED = StoredStrategy(
    holdings=HOLDINGS,
    targets=[
        TargetRow(symbol=h.symbol, current=c)
        for h, c in zip(HOLDINGS, (60, 30, 10), strict=True)
    ],
    targets_total=100,
    rule_checks=RuleChecks(met=0, enabled=0, rules=[]),
    proposal=None,
    notice=store.SAMPLE_NOTICE,
)
NOW = datetime(2026, 11, 24, 1, 30, tzinfo=UTC)


def _quote(price: str, minute: int = 30) -> Quote:
    return Quote(
        "2330.TW", Decimal(price), Decimal("1495"), "live", NOW.replace(minute=minute)
    )


@pytest.fixture
def reads(monkeypatch: pytest.MonkeyPatch) -> list[int]:
    made: list[int] = []

    async def read() -> StoredStrategy:
        made.append(1)
        return STORED

    monkeypatch.setattr(store, "read_strategy", read)
    return made


class _Prices:
    """Reads its closes, then streams until stopped, as the real feed does."""

    def __init__(
        self, *quotes: Quote, fail: bool = False, reading_seconds: float = 0
    ) -> None:
        self.quotes = quotes
        self.fail = fail
        self.reading_seconds = reading_seconds
        self.symbols: list[str] = []
        self.streaming = False
        self.stopped = False

    async def read_closes(
        self, symbols: list[str], on_quote: Callable[[Quote], None]
    ) -> None:
        self.symbols = symbols
        await asyncio.sleep(self.reading_seconds)
        for quote in self.quotes:
            on_quote(quote)

    async def stream(
        self,
        symbols: list[str],
        on_quote: Callable[[Quote], None],
        on_open: Callable[[bool], None],
    ) -> None:
        self.streaming = True
        if self.fail:
            raise ConnectionError("gone")
        on_open(True)
        try:
            await asyncio.Event().wait()
        finally:
            on_open(False)
            self.stopped = True


async def _settle() -> None:
    for _ in range(10):
        await asyncio.sleep(0)


def test_a_price_change_sends_the_view_and_reads_nothing_more(reads: list[int]) -> None:
    sent: list[StrategyView] = []

    async def main() -> None:
        state = StrategyState()

        async def listener(view: StrategyView) -> None:
            sent.append(view)

        await state.start(None, [listener])
        await state.view()
        state.price(_quote("1480"))
        await _settle()
        state.price(_quote("1480"))
        await _settle()
        state.price(_quote("1490", minute=31))
        await _settle()
        await state.stop()

    asyncio.run(main())

    assert reads == [1]
    assert [view.valuation.holdings[0].price for view in sent] == [
        Decimal("1480"),
        Decimal("1490"),
    ]


def test_after_a_write_the_strategy_is_read_again_once(reads: list[int]) -> None:
    async def main() -> None:
        state = StrategyState()
        await state.start(None, [])
        await state.view()
        state.written(STORED)
        await state.view()
        state.written()
        await state.view()
        await state.view()
        await state.stop()

    asyncio.run(main())

    assert reads == [1, 1]


def test_the_feed_gets_the_priced_symbols_and_is_stopped(reads: list[int]) -> None:
    feed = _Prices(_quote("1480"))
    seen: list[Decimal | None] = []

    async def main() -> None:
        state = StrategyState()
        await state.start(feed, [])
        await _settle()
        seen.append((await state.view()).valuation.holdings[0].price)
        await state.stop()

    asyncio.run(main())

    assert feed.symbols == ["2330.TW", "NVDA", "^SOX", "TWD=X"]
    assert seen == [Decimal("1480")]
    assert feed.stopped


def test_a_feed_that_fails_is_logged_and_the_service_goes_on(
    reads: list[int], caplog: pytest.LogCaptureFixture
) -> None:
    async def main() -> None:
        state = StrategyState()
        await state.start(_Prices(_quote("1480"), fail=True), [])
        await _settle()
        assert (await state.view()).valuation.holdings[0].price == Decimal("1480")
        await state.stop()

    asyncio.run(main())

    assert "The price feed stopped." in caplog.text


def test_without_a_profile_no_prices_are_read(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    async def missing() -> StoredStrategy:
        raise store.ProfileMissingError()

    monkeypatch.setattr(store, "read_strategy", missing)
    feed = _Prices(_quote("1480"))

    async def main() -> None:
        state = StrategyState()
        await state.start(feed, [])
        await _settle()
        await state.stop()

    asyncio.run(main())

    assert feed.symbols == []


def test_the_closes_are_in_before_the_service_takes_requests(reads: list[int]) -> None:
    feed = _Prices(_quote("1480"))

    async def main() -> Decimal | None:
        state = StrategyState()
        await state.start(feed, [])
        price = (await state.view()).valuation.holdings[0].price
        await state.stop()
        return price

    assert asyncio.run(main()) == Decimal("1480")


def test_slow_closes_do_not_hold_the_service_and_the_stream_starts(
    reads: list[int],
    monkeypatch: pytest.MonkeyPatch,
    caplog: pytest.LogCaptureFixture,
) -> None:
    monkeypatch.setattr(state_module, "CLOSES_WAIT_SECONDS", 0.05)
    feed = _Prices(_quote("1480"), reading_seconds=5)

    async def main() -> float:
        state = StrategyState()
        began = time.perf_counter()
        await state.start(feed, [])
        waited = time.perf_counter() - began
        await _settle()
        await state.stop()
        return waited

    assert asyncio.run(main()) < 1
    assert feed.streaming
    assert "were not all read within" in caplog.text


def test_the_page_is_told_when_the_live_stream_opens_and_ends(reads: list[int]) -> None:
    sent: list[bool] = []

    async def main() -> None:
        state = StrategyState()

        async def listener(view: StrategyView) -> None:
            sent.append(view.valuation.live)

        await state.start(_Prices(), [listener])
        await _settle()
        live_now = (await state.view()).valuation.live
        state.live(False)
        await _settle()
        state.live(False)
        await _settle()
        await state.stop()
        assert live_now

    asyncio.run(main())

    # Sent when it opened and when it ended; the same state twice is not sent again.
    assert sent == [True, False]


def test_a_read_that_a_write_overtook_is_not_kept(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    newer = STORED.model_copy(update={"proposal": None, "targets": STORED.targets[:1]})
    reads: list[StoredStrategy] = []

    async def main() -> list[int]:
        state = StrategyState()
        await state.start(None, [])
        reading = asyncio.Event()
        release = asyncio.Event()

        async def slow_read() -> StoredStrategy:
            reads.append(STORED)
            reading.set()
            await release.wait()
            return STORED

        monkeypatch.setattr(store, "read_strategy", slow_read)
        view = asyncio.create_task(state.view())
        await reading.wait()
        # A write lands while the read is still out.
        state.written(newer)
        release.set()
        await view
        targets = [len((await state.view()).targets)]
        await state.stop()
        return targets

    assert asyncio.run(main()) == [1]
    assert len(reads) == 1


class _Following(_Prices):
    """Has a close for every series it is asked for, and records each read of closes and each
    stream, so a restart on other holdings can be seen; it can fail every read after the first."""

    def __init__(self, *, fail_later_reads: bool = False) -> None:
        super().__init__()
        self.fail_later_reads = fail_later_reads
        self.reads: list[list[str]] = []
        self.streams: list[list[str]] = []

    async def read_closes(
        self, symbols: list[str], on_quote: Callable[[Quote], None]
    ) -> None:
        self.reads.append(symbols)
        if self.fail_later_reads and len(self.reads) > 1:
            raise ConnectionError("Yahoo is out of reach")
        for symbol in symbols:
            on_quote(Quote(symbol, Decimal("100"), Decimal("99"), "daily", NOW))

    async def stream(
        self,
        symbols: list[str],
        on_quote: Callable[[Quote], None],
        on_open: Callable[[bool], None],
    ) -> None:
        self.streams.append(symbols)
        await super().stream(symbols, on_quote, on_open)


# The sample's holdings with NVDA sold and AAPL bought.
SAVED = [HOLDINGS[0], HOLDINGS[1].model_copy(update={"symbol": "AAPL"}), HOLDINGS[2]]
STARTED = ["2330.TW", "NVDA", "^SOX", "TWD=X"]


async def _until(done: Callable[[], bool]) -> None:
    for _ in range(200):
        if done():
            return
        await asyncio.sleep(0)
    raise AssertionError("the feed did not get there")


def _follow(feed: _Following, holdings: list[HoldingView]) -> None:
    async def main() -> None:
        state = StrategyState()
        await state.start(feed, [])
        await _until(lambda: len(feed.streams) == 1)
        state.follow(holdings)
        await _until(lambda: len(feed.streams) == 2)
        await state.stop()

    asyncio.run(main())


def test_after_a_save_the_closes_of_the_new_holdings_are_read_and_the_stream_follows_them(
    reads: list[int],
) -> None:
    feed = _Following()

    _follow(feed, SAVED)

    assert feed.reads == [STARTED, ["AAPL"]]
    assert feed.streams == [STARTED, ["2330.TW", "AAPL", "^SOX", "TWD=X"]]
    assert feed.stopped


def test_holdings_saved_with_the_same_symbols_leave_the_feed_as_it_is(
    reads: list[int],
) -> None:
    feed = _Following()

    async def main() -> None:
        state = StrategyState()
        await state.start(feed, [])
        await _until(lambda: len(feed.streams) == 1)
        state.follow(HOLDINGS)
        await _settle()
        await state.stop()

    asyncio.run(main())

    assert feed.reads == [STARTED]
    assert feed.streams == [STARTED]


def test_closes_that_cannot_be_read_after_a_save_are_logged_and_the_stream_still_follows(
    reads: list[int], caplog: pytest.LogCaptureFixture
) -> None:
    feed = _Following(fail_later_reads=True)

    _follow(feed, SAVED)

    assert feed.streams[-1] == ["2330.TW", "AAPL", "^SOX", "TWD=X"]
    assert "could not be read" in caplog.text
