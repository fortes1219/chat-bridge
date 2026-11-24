"""Prices from the daily series and the live stream, with yfinance replaced by stand-ins: no
network is reached.
"""

import asyncio
import threading
from collections.abc import Callable
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from chat_bridge.config import local_data_dir
from chat_bridge.strategy import prices
from chat_bridge.strategy.prices import (
    PriceBook,
    Quote,
    YahooPrices,
    quote_from_history,
    quote_from_message,
)

TAIPEI = ZoneInfo("Asia/Taipei")
# 2026-11-24 09:30:00 in Taipei.
MILLIS = "1795483800000"
MOMENT = datetime(2026, 11, 24, 1, 30, tzinfo=UTC)


def _message(**fields: Any) -> dict[str, Any]:
    message: dict[str, Any] = {
        "id": "2330.TW",
        "price": 1480.0000610351562,
        "time": MILLIS,
        "price_hint": "2",
        "change": -15.0,
    }
    message.update(fields)
    return {key: value for key, value in message.items() if value is not None}


def _closes(*values: float, zone: ZoneInfo = TAIPEI) -> pd.DataFrame:
    days = pd.date_range("2026-11-19", periods=len(values), freq="D", tz=zone)
    return pd.DataFrame({"Close": list(values)}, index=days)


def test_a_float_price_becomes_a_decimal_rounded_by_its_hint() -> None:
    quote = quote_from_message(_message())

    assert quote == Quote(
        symbol="2330.TW",
        price=Decimal("1480.00"),
        previous_close=Decimal("1495.00"),
        basis="live",
        at=MOMENT,
    )


@pytest.mark.parametrize(
    "fields",
    [
        {"id": None},
        {"id": ""},
        {"price": None},
        {"price": True},
        {"price": "1480"},
        {"time": None},
        {"time": "soon"},
        {"price_hint": None},
        {"price_hint": "-1"},
    ],
)
def test_a_message_without_a_symbol_price_time_or_hint_is_dropped(
    fields: dict[str, Any],
) -> None:
    assert quote_from_message(_message(**fields)) is None


def test_a_message_yfinance_could_not_decode_is_dropped() -> None:
    assert quote_from_message({"error": "bad", "raw_base64": "xx"}) is None


def test_a_message_without_the_change_says_no_previous_close() -> None:
    quote = quote_from_message(_message(change=None))

    assert quote is not None
    assert quote.previous_close is None


def test_the_daily_series_gives_the_last_close_and_the_one_before_on_the_exchange_day() -> (
    None
):
    quote = quote_from_history("2330.TW", _closes(1470.0, float("nan"), 1495.0, 1480.5))

    assert quote is not None
    assert quote.price == Decimal("1480.5")
    assert quote.previous_close == Decimal("1495")
    assert quote.basis == "daily"
    # The trading day as Taipei names it, not as UTC would.
    assert quote.at.date().isoformat() == "2026-11-22"


def test_a_missing_day_before_the_latest_leaves_the_previous_close_unknown() -> None:
    # Yahoo had no close for the day before; the close of the day before that would make a
    # two-day move look like one day's.
    quote = quote_from_history("006208.TW", _closes(202.65, 189.8, float("nan"), 215.1))

    assert quote is not None
    assert quote.price == Decimal("215.1")
    assert quote.previous_close is None


def test_a_latest_day_without_a_close_leaves_the_day_before_as_the_latest() -> None:
    quote = quote_from_history("2330.TW", _closes(1470.0, 1495.0, float("nan")))

    assert quote is not None
    assert quote.price == Decimal("1495")
    assert quote.previous_close == Decimal("1470")
    assert quote.at.date().isoformat() == "2026-11-20"


@pytest.mark.parametrize(
    "frame",
    [
        pd.DataFrame(),
        pd.DataFrame({"Close": []}),
        _closes(float("nan")),
    ],
)
def test_a_series_without_a_close_gives_no_price(frame: pd.DataFrame) -> None:
    assert quote_from_history("2330.TW", frame) is None


def test_one_close_gives_no_previous_close() -> None:
    quote = quote_from_history("2330.TW", _closes(1480.0))

    assert quote is not None
    assert quote.previous_close is None


def _quote(price: str, at: datetime, previous: str | None = "1495") -> Quote:
    return Quote(
        symbol="2330.TW",
        price=Decimal(price),
        previous_close=None if previous is None else Decimal(previous),
        basis="live",
        at=at,
    )


def test_the_book_keeps_the_latest_quote_and_says_when_it_changed() -> None:
    book = PriceBook()
    later = MOMENT.replace(minute=40)

    assert book.put(_quote("1480", MOMENT))
    assert not book.put(_quote("1480", MOMENT))
    assert book.put(_quote("1485", later))
    assert not book.put(_quote("1470", MOMENT))
    assert book.get("2330.TW") == _quote("1485", later)


def test_a_live_price_without_a_previous_close_keeps_the_known_one() -> None:
    book = PriceBook()
    book.put(_quote("1480", MOMENT))

    book.put(_quote("1485", MOMENT.replace(minute=40), previous=None))

    quote = book.get("2330.TW")
    assert quote is not None
    assert quote.previous_close == Decimal("1495")


class _Ticker:
    calls: list[tuple[str, dict[str, Any]]] = []

    def __init__(self, symbol: str) -> None:
        self.symbol = symbol

    def history(self, **options: Any) -> pd.DataFrame:
        _Ticker.calls.append((self.symbol, options))
        if self.symbol == "NVDA":
            raise ConnectionError("no route to host")
        return _closes(1495.0, 1480.0)


class _Stream:
    """yfinance's synchronous WebSocket: `listen` blocks until `close`, as a real one does."""

    made: list["_Stream"] = []
    # How each new stream behaves, in order: "fail" to fail when subscribing, or the messages
    # it sends.
    plan: list[str | list[dict[str, Any]]] = []

    def __init__(self, verbose: bool = True) -> None:
        self.verbose = verbose
        self.subscriptions: list[list[str]] = []
        self.closed = threading.Event()
        self.behaviour = _Stream.plan.pop(0) if _Stream.plan else []
        _Stream.made.append(self)

    def subscribe(self, symbols: list[str]) -> None:
        if self.behaviour == "fail":
            raise OSError("network is unreachable")
        self.subscriptions.append(list(symbols))

    def listen(self, handler: Callable[[dict[str, Any]], None]) -> None:
        for message in self.behaviour:
            assert isinstance(message, dict)
            handler(message)
        self.closed.wait(timeout=5)

    def close(self) -> None:
        self.closed.set()


# The folders yfinance was told to keep its caches in.
_caches: list[str] = []


@pytest.fixture
def stand_in_yfinance(monkeypatch: pytest.MonkeyPatch) -> None:
    _caches.clear()
    opened.clear()
    _Ticker.calls = []
    _Stream.made = []
    _Stream.plan = []
    stand_in = SimpleNamespace(
        Ticker=_Ticker, WebSocket=_Stream, set_tz_cache_location=_caches.append
    )
    monkeypatch.setattr(prices, "yf", stand_in)
    monkeypatch.setattr(prices, "RECONNECT_SECONDS", 0)


# What the stream said of its connection in the last run: true when it opened, false when it ended.
opened: list[bool] = []


def _run_until(
    source: YahooPrices, symbols: list[str], done: Callable[[list[Quote]], bool]
) -> list[Quote]:
    """Run the source until `done` holds for the quotes it sent, then stop it as the service
    does."""
    received: list[Quote] = []

    async def run() -> None:
        await source.read_closes(symbols, received.append)
        await source.stream(symbols, received.append, opened.append)

    async def main() -> None:
        task = asyncio.create_task(run())
        async with asyncio.timeout(5):
            while not done(received):
                await asyncio.sleep(0.01)
        task.cancel()
        with pytest.raises(asyncio.CancelledError):
            await task

    asyncio.run(main())
    return received


def test_recent_closes_come_first_unadjusted_and_a_failing_symbol_is_missing(
    stand_in_yfinance: None,
) -> None:
    _Stream.plan = [[_message(id="2308.TW", price=1201.0)]]

    received = _run_until(
        YahooPrices(), ["2330.TW", "NVDA", "2308.TW"], lambda got: len(got) == 3
    )

    assert [(quote.symbol, quote.basis) for quote in received] == [
        ("2330.TW", "daily"),
        ("2308.TW", "daily"),
        ("2308.TW", "live"),
    ]
    assert {options["auto_adjust"] for _, options in _Ticker.calls} == {False}
    # The days Yahoo has no close for are kept, so a missing day is seen as missing.
    assert {options["keepna"] for _, options in _Ticker.calls} == {True}
    # Its caches go to the service's local data folder, not the user's own cache folder.
    assert _caches == [str(local_data_dir() / "yfinance")]


def test_the_stream_is_quiet_subscribed_to_every_symbol_and_closed_when_stopped(
    stand_in_yfinance: None,
) -> None:
    _Stream.plan = [[_message()]]

    _run_until(
        YahooPrices(),
        ["2330.TW", "NVDA"],
        lambda got: got[-1:] != [] and got[-1].basis == "live",
    )

    stream = _Stream.made[0]
    assert opened[0] is True
    assert not stream.verbose
    assert stream.subscriptions[0] == ["2330.TW", "NVDA"]
    assert stream.closed.is_set()


def test_a_stream_that_cannot_be_opened_is_opened_again_and_says_so_once(
    stand_in_yfinance: None, caplog: pytest.LogCaptureFixture
) -> None:
    _Stream.plan = ["fail", "fail", "fail", [_message()]]

    with caplog.at_level("INFO", logger="chat_bridge.strategy.prices"):
        received = _run_until(
            YahooPrices(), ["2330.TW"], lambda got: any(q.basis == "live" for q in got)
        )

    assert len(_Stream.made) == 4
    assert received[-1].basis == "live"
    assert all(stream.closed.is_set() for stream in _Stream.made)
    # Three failures in a row are said once, and the recovery once.
    assert caplog.text.count("could not be opened") == 1
    assert caplog.text.count("open again") == 1
    # The page is told the stream is closed until it opens.
    assert opened[:3] == [False, False, False]
    assert True in opened


def test_a_stream_that_ends_is_opened_again_and_subscribed_again(
    stand_in_yfinance: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    ending = _Stream.__init__

    def ends_at_once(self: _Stream, verbose: bool = True) -> None:
        ending(self, verbose)
        if len(_Stream.made) == 1:
            # The first connection ends as a dropped one does: `listen` returns.
            self.closed.set()

    monkeypatch.setattr(_Stream, "__init__", ends_at_once)
    _Stream.plan = [[], [_message()]]

    _run_until(
        YahooPrices(), ["2330.TW"], lambda got: any(q.basis == "live" for q in got)
    )

    assert [stream.subscriptions[0] for stream in _Stream.made] == [
        ["2330.TW"],
        ["2330.TW"],
    ]


def test_the_subscription_is_sent_again_while_the_stream_is_open(
    stand_in_yfinance: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    monkeypatch.setattr(prices, "RESUBSCRIBE_SECONDS", 0.01)
    _Stream.plan = [[]]

    _run_until(
        YahooPrices(),
        ["2330.TW"],
        lambda _: bool(_Stream.made) and len(_Stream.made[0].subscriptions) >= 3,
    )

    assert len(_Stream.made) == 1
    assert _Stream.made[0].subscriptions[1] == ["2330.TW"]


def test_messages_that_lack_a_field_are_dropped_and_counted(
    stand_in_yfinance: None,
) -> None:
    _Stream.plan = [[_message(price=None), _message(price_hint=None), _message()]]
    source = YahooPrices()

    received = _run_until(
        source, ["2330.TW"], lambda got: any(q.basis == "live" for q in got)
    )

    assert [quote.basis for quote in received] == ["daily", "live"]
    assert source.dropped == 2
