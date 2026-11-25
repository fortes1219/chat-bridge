"""Prices from the daily series and the live stream, with yfinance replaced by stand-ins: no
network is reached.
"""

import asyncio
import threading
from collections.abc import Callable
from datetime import UTC, date, datetime
from decimal import Decimal
from types import SimpleNamespace
from typing import Any
from zoneinfo import ZoneInfo

import pandas as pd
import pytest

from chat_bridge.config import local_data_dir
from chat_bridge.strategy import prices
from chat_bridge.strategy.history import History
from chat_bridge.strategy.prices import (
    PriceBook,
    Quote,
    YahooPrices,
    history_from_frame,
    latest_quote,
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


# A day after every day of the series above, so none of them was read while it traded.
READ_ON = date(2026, 11, 25)


def quote_from_history(symbol: str, frame: pd.DataFrame) -> Quote | None:
    """The latest daily value Yahoo's series alone gives, as the service reads it."""
    return latest_quote(symbol, history_from_frame(symbol, frame, READ_ON))


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
    # Yahoo's own quote: no previous close, unless a test says otherwise.
    fast_info = SimpleNamespace(regular_market_previous_close=None, previous_close=None)

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

    # No network: the Taiwan sources add nothing in these tests; the ones below that need them
    # replace the sources themselves.
    async def no_taiwan_sources(*arguments: Any) -> None:
        pass

    monkeypatch.setattr(prices, "add_taiwan_sources", no_taiwan_sources)


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


# Spec 012: where the previous close comes from.
TODAY = date(2026, 11, 25)
# Yahoo's series of 0050 as it was on 2026-11-25: no close for 11-24.
YAHOO_0050 = History(
    read_on=TODAY,
    closes={date(2026, 11, 23): Decimal("87.00"), TODAY: Decimal("90.30")},
    missing=frozenset({date(2026, 11, 24)}),
)
FINMIND_0050 = History(
    read_on=TODAY,
    closes={
        date(2026, 11, 23): Decimal("87.0"),
        date(2026, 11, 24): Decimal("95.7"),
        TODAY: Decimal("90.3"),
    },
)


class _Sources:
    """FinMind, the notices and the daily tables, each answering or failing as a test says."""

    def __init__(
        self, monkeypatch: pytest.MonkeyPatch, *, finmind: bool = True
    ) -> None:
        self.read: list[str] = []
        self.finmind = finmind
        monkeypatch.setattr(prices, "finmind_history", self.finmind_history)
        monkeypatch.setattr(prices, "notices", self.notices)
        monkeypatch.setattr(prices, "daily_tables", self.daily_tables)

    def finmind_history(self, symbol: str, today: date) -> History:
        self.read.append(f"finmind {symbol}")
        if not self.finmind:
            raise prices.SourceError("Requests reach the upper limit.")
        return FINMIND_0050

    def notices(self, symbols: list[str], today: date) -> dict[str, Any]:
        self.read.append("notices")
        return {}

    def daily_tables(
        self, symbols: list[str], today: date, dividends: dict[str, Any]
    ) -> dict[str, History]:
        self.read.append(f"tables {symbols}")
        return {
            "0050.TW": History(
                read_on=TODAY,
                closes={date(2026, 11, 24): Decimal("95.70")},
                given={date(2026, 11, 24): Decimal("87.00")},
            )
        }


def _add_taiwan(
    symbols: list[str], histories: dict[str, History]
) -> tuple[dict[str, History], list[str]]:
    """The series' days after the Taiwan sources, and the series told as they grew."""
    found = dict(histories)
    changed: list[str] = []
    asyncio.run(prices.add_taiwan_sources(symbols, found, TODAY, changed.append))
    return found, changed


def test_finmind_gives_the_previous_close_yahoos_series_lacked(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sources = _Sources(monkeypatch)

    found, changed = _add_taiwan(["0050.TW"], {"0050.TW": YAHOO_0050})

    quote = latest_quote("0050.TW", found["0050.TW"])
    assert quote is not None
    assert (quote.price, quote.previous_close) == (Decimal("90.3"), Decimal("95.7"))
    # FinMind had it, so the daily tables are not read.
    assert sources.read == ["finmind 0050.TW", "notices"]
    assert changed == ["0050.TW"]


def test_once_finmind_fails_it_is_not_asked_for_the_other_series(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sources = _Sources(monkeypatch, finmind=False)

    _add_taiwan(["0050.TW", "006208.TW"], {})

    assert sources.read == [
        "finmind 0050.TW",
        "notices",
        "tables ['0050.TW', '006208.TW']",
    ]


def test_a_close_finmind_has_and_yahoo_has_not_yet_is_the_latest_with_its_day(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    _Sources(monkeypatch)
    yahoo = History(
        read_on=TODAY,
        closes={date(2026, 11, 23): Decimal("87.00")},
        missing=frozenset({date(2026, 11, 24)}),
    )

    found, _ = _add_taiwan(["0050.TW"], {"0050.TW": yahoo})

    quote = latest_quote("0050.TW", found["0050.TW"])
    assert quote is not None
    assert (quote.price, quote.at.date(), quote.previous_close) == (
        Decimal("90.3"),
        TODAY,
        Decimal("95.7"),
    )


def test_without_finmind_the_exchanges_daily_table_gives_it(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    sources = _Sources(monkeypatch, finmind=False)

    found, _ = _add_taiwan(["0050.TW"], {"0050.TW": YAHOO_0050})

    assert found["0050.TW"].previous_close(TODAY) == Decimal("95.70")
    assert sources.read == ["finmind 0050.TW", "notices", "tables ['0050.TW']"]


def test_a_us_series_reads_no_taiwan_source(monkeypatch: pytest.MonkeyPatch) -> None:
    sources = _Sources(monkeypatch)
    nvda = History(read_on=TODAY)

    assert _add_taiwan(["NVDA"], {"NVDA": nvda}) == ({"NVDA": nvda}, [])
    assert sources.read == []


def test_yahoos_own_quote_is_the_last_source(
    stand_in_yfinance: None, monkeypatch: pytest.MonkeyPatch
) -> None:
    # A series missing the day before its latest, which no other source fills.
    monkeypatch.setattr(
        _Ticker,
        "history",
        lambda self, **options: _closes(165.05, float("nan"), 155.38),
    )
    monkeypatch.setattr(
        _Ticker,
        "fast_info",
        SimpleNamespace(
            regular_market_previous_close=165.0500030517578, previous_close=165.2596
        ),
    )
    received: list[Quote] = []

    asyncio.run(YahooPrices().read_closes(["NVDA"], received.append))

    # The price is sent from the series first, then with the quote's previous close.
    assert [quote.previous_close for quote in received] == [None, Decimal("165.0500")]


def test_a_taiwan_source_that_does_not_answer_holds_back_no_price_from_yahoo(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    # yfinance answers; FinMind does not, until the test lets it.
    monkeypatch.setattr(
        prices,
        "yf",
        SimpleNamespace(Ticker=_Ticker, set_tz_cache_location=lambda folder: None),
    )
    monkeypatch.setattr(
        _Ticker, "history", lambda self, **options: _closes(1495.0, 1480.0)
    )
    answer = threading.Event()

    def finmind_history(symbol: str, today: date) -> History:
        answer.wait(timeout=5)
        raise prices.SourceError("timed out")

    monkeypatch.setattr(prices, "finmind_history", finmind_history)
    monkeypatch.setattr(prices, "notices", lambda symbols, today: {})
    monkeypatch.setattr(prices, "daily_tables", lambda symbols, today, dividends: {})
    received: list[Quote] = []

    async def main() -> set[str]:
        reading = asyncio.create_task(
            YahooPrices().read_closes(["2330.TW", "NVDA"], received.append)
        )
        try:
            async with asyncio.timeout(2):
                while len(received) < 2:
                    await asyncio.sleep(0.01)
            return {quote.symbol for quote in received}
        finally:
            answer.set()
            await reading

    # Both prices arrive while FinMind has not answered.
    assert asyncio.run(main()) == {"2330.TW", "NVDA"}


def test_a_live_price_takes_the_previous_close_of_its_day_from_the_series_days() -> (
    None
):
    book = PriceBook()
    daily = latest_quote("0050.TW", FINMIND_0050)
    assert daily is not None
    book.put(daily)

    # The stream works its previous close out from its own change; the series' days win.
    live = Quote(
        "0050.TW",
        Decimal("90.50"),
        Decimal("96.00"),
        "live",
        datetime(2026, 11, 25, 2, tzinfo=UTC),
    )
    assert book.put(live)

    quote = book.get("0050.TW")
    assert quote is not None
    assert (quote.price, quote.previous_close) == (Decimal("90.50"), Decimal("95.7"))
    assert not book.needs_days(live)
    tomorrow = Quote(
        "0050.TW", Decimal("91"), None, "live", datetime(2026, 11, 26, 2, tzinfo=UTC)
    )
    assert book.needs_days(tomorrow)


def test_days_that_arrive_after_a_later_price_still_give_it_its_previous_close() -> (
    None
):
    book = PriceBook()
    live = Quote(
        "0050.TW", Decimal("90.50"), None, "live", datetime(2026, 11, 25, 2, tzinfo=UTC)
    )
    book.put(live)
    daily = latest_quote("0050.TW", FINMIND_0050)
    assert daily is not None

    # The daily value is older than the live price, but its days give the previous close.
    assert book.put(daily)

    quote = book.get("0050.TW")
    assert quote is not None
    assert (quote.basis, quote.previous_close) == ("live", Decimal("95.7"))


def test_a_currency_pairs_days_are_the_days_yahoo_names_in_london() -> None:
    # TWD=X as Yahoo gave it on 2026-11-25: each value at 00:00 in London.
    london = ZoneInfo("Europe/London")
    days = pd.DatetimeIndex(
        [datetime(2026, 11, day, tzinfo=london) for day in (19, 20, 23, 24, 25)]
    )
    frame = pd.DataFrame({"Close": [32.9, 32.95, 32.8, 32.8485, 33.126]}, index=days)
    book = PriceBook()
    daily = latest_quote("TWD=X", history_from_frame("TWD=X", frame, READ_ON))
    assert daily is not None
    book.put(daily)

    assert (daily.at.date(), daily.price, daily.previous_close) == (
        READ_ON,
        Decimal("33.126"),
        Decimal("32.8485"),
    )
    # A live rate at 10:00 in London on 11-25 is measured from 11-24's value.
    book.put(
        Quote(
            "TWD=X",
            Decimal("33.15"),
            Decimal("32.8485"),
            "live",
            datetime(2026, 11, 25, 10, tzinfo=UTC),
        )
    )
    quote = book.get("TWD=X")
    assert quote is not None
    assert quote.previous_close == Decimal("32.8485")


def test_a_us_price_outside_the_regular_session_is_measured_from_the_last_regular_close() -> (
    None
):
    book = PriceBook()
    daily = latest_quote(
        "NVDA",
        History(
            read_on=TODAY,
            closes={
                date(2026, 11, 23): Decimal("165.05"),
                date(2026, 11, 24): Decimal("155.38"),
            },
        ),
    )
    assert daily is not None
    book.put(daily)
    measured_from: list[Decimal | None] = []
    # In New York: 11-24 at 20:30 (evening), 11-25 at 00:30 (overnight) and 08:00 (pre-market).
    for moment in (
        datetime(2026, 11, 25, 1, 30, tzinfo=UTC),
        datetime(2026, 11, 25, 5, 30, tzinfo=UTC),
        datetime(2026, 11, 25, 13, 0, tzinfo=UTC),
    ):
        book.put(Quote("NVDA", Decimal("154.60"), Decimal("155.38"), "live", moment))
        quote = book.get("NVDA")
        measured_from.append(None if quote is None else quote.previous_close)

    # The day's close, from the evening on: nothing moves at midnight in New York.
    assert measured_from == [Decimal("155.38")] * 3
    assert daily.previous_close == Decimal("165.05")


def test_a_live_price_of_a_day_after_the_days_were_read_keeps_its_own_previous_close() -> (
    None
):
    # Read on 11-24 before it opened: the sources had up to 11-23.
    book = PriceBook()
    daily = latest_quote(
        "0050.TW",
        History(
            read_on=date(2026, 11, 24),
            closes={
                date(2026, 11, 20): Decimal("84.45"),
                date(2026, 11, 23): Decimal("87.00"),
            },
        ),
    )
    assert daily is not None
    book.put(daily)

    book.put(
        Quote(
            "0050.TW",
            Decimal("90.30"),
            Decimal("95.70"),
            "live",
            datetime(2026, 11, 25, 2, tzinfo=UTC),
        )
    )

    # 11-23's close is not 11-25's previous close; the stream's own is kept.
    quote = book.get("0050.TW")
    assert quote is not None
    assert quote.previous_close == Decimal("95.70")
