"""Taiwan daily closes and reference prices, from FinMind's public API and the exchanges' open data.

FinMind gives a month of daily closes and each ex-dividend day's reference price, with no key, 300
requests an hour. The Taiwan Stock Exchange (listed) and the Taipei Exchange (OTC) give, in their
open-data APIs, every security's latest day and each market's advance notice of ex-dividend and
ex-rights days. Only past closes and reference prices are read; FinMind's terms forbid showing its
real-time data on a public interface or passing its data on.

Each request is a plain GET with requests, as FinMind's own package sends it. A source that cannot
be read raises SourceError, and the caller goes on with the next source. A row in another shape
than the source's own, or without a day or a price, is left out.
"""

from __future__ import annotations

from collections.abc import Iterable
from datetime import date, timedelta
from decimal import Decimal, InvalidOperation
from typing import Any

import requests

from chat_bridge.strategy.history import History

FINMIND_URL = "https://api.finmindtrade.com/api/v4/data"
LISTED_DAILY_URL = "https://openapi.twse.com.tw/v1/exchangeReport/STOCK_DAY_ALL"
LISTED_NOTICES_URL = "https://openapi.twse.com.tw/v1/exchangeReport/TWT48U_ALL"
OTC_DAILY_URL = "https://www.tpex.org.tw/openapi/v1/tpex_mainboard_daily_close_quotes"
OTC_NOTICES_URL = "https://www.tpex.org.tw/openapi/v1/tpex_exright_prepost"
# As yfinance's own default for a daily series: a source that does not answer holds neither the
# other sources nor the service's stop for long.
TIMEOUT_SECONDS = 10
# Daily closes for about a month, so a long holiday still leaves a previous close.
HISTORY_DAYS = 40
OTC_SUFFIX = ".TWO"
# The words each market's advance notice uses for a cash dividend alone; any other kind (stock
# dividend, rights issue, both) has no reference price that can be worked out from the notice.
CASH_ONLY = {"listed": "息", "otc": "除息"}


class SourceError(Exception):
    """A source that could not be read or answered something else than its data."""


def is_otc(symbol: str) -> bool:
    return symbol.endswith(OTC_SUFFIX)


def code_of(symbol: str) -> str:
    """The exchange's code of a Yahoo symbol: 6488.TWO and 2330.TW are 6488 and 2330."""
    return symbol.split(".", 1)[0]


def _get(url: str, params: dict[str, str] | None = None) -> Any:
    try:
        response = requests.get(url, params=params, timeout=TIMEOUT_SECONDS)
        response.raise_for_status()
        return response.json()
    except (requests.RequestException, ValueError) as error:
        raise SourceError(f"{url}: {error}") from error


def _number(value: object) -> Decimal | None:
    """A price as an exact decimal; None for anything else, such as an ex-dividend day's 'X0.00'."""
    if isinstance(value, bool) or not isinstance(value, int | float | str):
        return None
    try:
        number = Decimal(str(value).strip().removeprefix("+"))
    except InvalidOperation:
        return None
    return number if number.is_finite() else None


def _rows(value: object) -> list[dict[str, Any]]:
    """The rows of a table that are objects; anything else in it is not data."""
    if not isinstance(value, list):
        return []
    return [row for row in value if isinstance(row, dict)]


def _iso_date(text: object) -> date | None:
    try:
        return date.fromisoformat(str(text))
    except ValueError:
        return None


def _roc_date(text: object) -> date | None:
    """A date the exchanges write in the Republic of China calendar: 1151124 is 2026-11-24."""
    if not isinstance(text, str) or not text.isdigit() or len(text) < 7:
        return None
    try:
        return date(int(text[:-4]) + 1911, int(text[-4:-2]), int(text[-2:]))
    except ValueError:
        return None


def _finmind(
    dataset: str, code: str, start: date, end: date | None = None
) -> list[dict[str, Any]]:
    params = {"dataset": dataset, "data_id": code, "start_date": start.isoformat()}
    if end is not None:
        params["end_date"] = end.isoformat()
    body = _get(FINMIND_URL, params)
    data = body.get("data") if isinstance(body, dict) else None
    if (
        not isinstance(body, dict)
        or body.get("status") != 200
        or not isinstance(data, list)
    ):
        message = body.get("msg") if isinstance(body, dict) else body
        raise SourceError(f"FinMind {dataset}: {message}")
    return _rows(data)


def finmind_closes(
    code: str, start: date, end: date | None = None
) -> dict[date, Decimal]:
    """FinMind's daily closes of a Taiwan code (a stock, an ETF, or TAIEX for the index) from
    `start` to `end`. A code FinMind does not know gives none. Raises SourceError."""
    closes: dict[date, Decimal] = {}
    for row in _finmind("TaiwanStockPrice", code, start, end):
        day, close = _iso_date(row.get("date")), _number(row.get("close"))
        if day is not None and close is not None and close > 0:
            closes[day] = close
    return closes


def finmind_history(symbol: str, today: date) -> History:
    """A month of FinMind's daily closes of a Taiwan series, and the reference price of each
    ex-dividend or ex-rights day in it. A code FinMind does not know gives an empty history.
    Raises SourceError."""
    start = today - timedelta(days=HISTORY_DAYS)
    code = code_of(symbol)
    closes = finmind_closes(code, start)
    given: dict[date, Decimal] = {}
    for row in _finmind("TaiwanStockDividendResult", code, start):
        day, reference = _iso_date(row.get("date")), _number(row.get("reference_price"))
        if day is not None and reference is not None and reference > 0:
            given[day] = reference
    return History(read_on=today, closes=closes, given=given)


def notices(
    symbols: Iterable[str], today: date
) -> dict[str, dict[date, Decimal | None]]:
    """The announced ex-dividend and ex-rights days from today on of the Taiwan symbols, from the
    advance notice of each market they are in: the cash dividend when it is the only one and its
    amount is given, else None. Raises SourceError."""
    by_code = {code_of(symbol): symbol for symbol in symbols}
    markets = {"otc" if is_otc(symbol) else "listed" for symbol in by_code.values()}
    found: dict[str, dict[date, Decimal | None]] = {}
    for market in sorted(markets):
        for row in _rows(
            _get(OTC_NOTICES_URL if market == "otc" else LISTED_NOTICES_URL)
        ):
            if market == "otc":
                code, day = (
                    row.get("SecuritiesCompanyCode"),
                    _roc_date(row.get("ExRrightsExDividendDate")),
                )
                kind = row.get("ExRrightsExDividend")
            else:
                code, day, kind = (
                    row.get("Code"),
                    _roc_date(row.get("Date")),
                    row.get("Exdividend"),
                )
            symbol = by_code.get(str(code))
            if symbol is None or day is None or day < today:
                continue
            cash = (
                _number(row.get("CashDividend")) if kind == CASH_ONLY[market] else None
            )
            found.setdefault(symbol, {})[day] = (
                cash if cash is not None and cash > 0 else None
            )
    return found


def daily_tables(
    symbols: Iterable[str],
    today: date,
    dividends: dict[str, dict[date, Decimal | None]],
) -> dict[str, History]:
    """Each Taiwan symbol's latest day from the open-data table of its market: the close, the
    previous close the change gives (not on an ex-dividend or ex-rights day, whose change is not
    measured from the close before), and the OTC market's next reference price. Raises
    SourceError."""
    by_code = {code_of(symbol): symbol for symbol in symbols}
    histories: dict[str, History] = {}
    for otc in sorted({is_otc(symbol) for symbol in by_code.values()}):
        for row in _rows(_get(OTC_DAILY_URL if otc else LISTED_DAILY_URL)):
            symbol = by_code.get(
                str(row.get("SecuritiesCompanyCode" if otc else "Code"))
            )
            day = _roc_date(row.get("Date"))
            close = _number(row.get("Close" if otc else "ClosingPrice"))
            if symbol is None or day is None or close is None or close <= 0:
                continue
            change = _number(row.get("Change"))
            given = (
                {}
                if change is None or day in dividends.get(symbol, {})
                else {day: close - change}
            )
            reference = _number(row.get("NextReferencePrice")) if otc else None
            histories[symbol] = History(
                read_on=today,
                closes={day: close},
                given=given,
                next_reference=None
                if reference is None or reference <= 0
                else (day, reference),
            )
    return histories
