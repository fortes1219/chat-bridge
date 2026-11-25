# Research: Previous closes

## Packages

No package is added: requests is already in the lock file, through yfinance; it becomes a declared
dependency. yfinance is already one.

| Need | Package | Version | License | Size | Dependency declared in | Called in |
|---|---|---|---|---|---|---|
| Read Taiwan daily closes and the reference prices of ex-dividend days from FinMind's public API | requests | 2.34.2 | Apache-2.0 | none added: already locked through yfinance | `FinMind/FinMind@d89a84a:pyproject.toml:30` | `FinMind/FinMind@d89a84a:FinMind/utility/request.py:31` |
| Read the latest day, the next reference prices and the ex-dividend notices from the Taiwan exchanges' open-data APIs | requests | 2.34.2 | Apache-2.0 | none added: already locked through yfinance | `FinMind/FinMind@d89a84a:pyproject.toml:30` | `FinMind/FinMind@d89a84a:FinMind/utility/request.py:31` |
| Read Yahoo's own quote of the previous close | yfinance | 1.8.0 | Apache-2.0 | none added: already a dependency | `TauricResearch/TradingAgents@9fa1196fffbc:pyproject.toml:30` | `TauricResearch/TradingAgents@9fa1196fffbc:tradingagents/dataflows/vendors/yahoo/market.py:6` |

## Advisories

requests 2.34.2: none (OSV, 2026-11-25). The lock file is checked again before delivery.

## Decisions

1. **Three sources, so "not known" is rare.** Measured on 2026-11-25:
   - FinMind's `TaiwanStockPrice` has every trading day of 0050, 006208 and the OTC stock 6488,
     2026-11-24 included (0050 95.7, 006208 215.1), and today's close; the numbers match the Taiwan
     Stock Exchange's open-data API (`STOCK_DAY_ALL`, 2026-11-24). Its `TaiwanStockDividendResult`
     gives each ex-dividend day's close before and reference price after (0050 2026-07-21: 99.2 and
     98.6), the same as the exchange's ex-dividend results. Without a token it answers 300 requests
     an hour (its README), and its terms say the free service may change or stop.
   - The exchanges' open-data APIs, which say they welcome programs and carry the open-data
     licence: the listed market's `STOCK_DAY_ALL` (every listed security's latest close and change,
     1,394 rows) and advance notice `TWT48U_ALL`; the OTC market's
     `tpex_mainboard_daily_close_quotes` (latest close, change and `NextReferencePrice`) and
     `tpex_exright_prepost`. They hold the latest day only, which is the day a previous close needs.
   - Yahoo's own quote: for 0050 and 006208 its `previous_close` was 95.70 and 215.10, the
     exchange's closes, while its daily series lacked that day; its
     `regular_market_previous_close` was empty for them. For NVDA, `regular_market_previous_close`
     was 165.05, the day's close, and `previous_close` 165.2596, not a close. So
     `regular_market_previous_close` is read first and `previous_close` when it is empty.
   - The exchanges' websites forbid programs in their terms, and their real-time service in its
     robots.txt; Fugle needs an account and a key.
2. **FinMind's API, not its package.** The package pulls in IPython, pyecharts, pyarrow, aiohttp
   and ta, among others; it reads the same API with requests (`FinMind/data/finmind_api.py:194`
   calls `FinMind/utility/request.py:31`).
3. **The previous close is the exchange's.** On an ex-dividend or ex-rights day a quote's change is
   measured from the reference price, as the exchange and brokers measure it. The exchange's own
   daily table writes that day's change as "X0.00" and FinMind's `spread` is 0, so the change is
   never taken from either.
4. **An ex-dividend day is known before its reference price.** The reference price of the day may
   be published after the day starts. The advance notices name the day beforehand: on it, a cash
   dividend alone gives the reference price as the previous close less the dividend; a stock
   dividend, a rights issue or a missing amount gives none, and the holding is named instead of
   being measured from the close before the dividend. The OTC market's `NextReferencePrice` gives
   the next day's reference price directly.
5. **requests reaches the exchanges as it is.** Python 3.13's `ssl.create_default_context()`
   refuses their certificates (strict X.509: no Subject Key Identifier); requests, through
   urllib3 2.8.0, read all four open-data tables with no change to certificate checking (measured).
6. **Terms.** FinMind's terms forbid showing its real-time data on a public interface,
   redistributing its raw data and building an equivalent service
   (https://finmind.github.io/en/PrivacyPolicy/ §4). The service reads only past closes and
   reference prices, on the person's own machine, and keeps them in memory.
7. **The words on the panel** say what is left out and why, in the person's terms (spec User Story
   3), not the program's.
8. **Inferred, not measured, and kept by the maintainer's decision (2026-11-25):** that FinMind's
   reference price of an ex-dividend day may come after the day starts (scenario 3); that Yahoo's
   US daily series may miss a day (scenario 9: the ten days read had none missing); that FinMind
   may not know a code (scenario 8); that the service may run from one day into the next
   (scenario 11). None of these was seen in a product or measured; each costs a fallback that
   follows the same order of sources. When the open-data daily tables change to the day is to be
   measured (task T007).
9. **Decided here, without a precedent:** once FinMind fails in a read, it is not asked for the
   other series in that read, as each request would wait as long, and the daily tables still
   follow. Each request to FinMind and the open data gives up after 10 seconds, yfinance's own
   default for a daily series (`yfinance/scrapers/history.py:112`, 1.8.0), so a source that does
   not answer holds neither the other sources nor the service's stop for long.
10. **A US price outside the regular session is measured from the last regular close.** Yahoo's
    stream measures it so (spec 006 research: NVIDIA past midnight in New York against the last
    regular close). A price from 16:00 New York on is measured as the next day's, so nothing
    moves at midnight; on an early-close day (13:00) a price before 16:00 is still measured from
    the day before's close, as the service has no exchange calendar. The sources are read again
    on a series' first price of a new calendar day where it trades, not of the day it is measured
    from: read that evening, they give the same day. So a US price of an evening, before
    midnight in New York, is measured from the stream's own previous close; one that does not
    say it has none until the sources are read on the next day (inferred, not measured). A
    currency pair's days are the days in London, as Yahoo dates them (TWD=X: exchange time zone
    Europe/London, each daily value at 00:00 there), and it has no session end.
11. **Naming the sources (FR-006).** Read on 2026-11-25:
    - The Open Government Data License (https://data.gov.tw/license, 3(2)): whoever uses the open
      data or what is made from it names the providing agency as its annex asks, or the license
      is void from the start. The annex, as the English page gives it: "Data Providing
      Organization/Agency [year] [distinguishing full name of the released Open Data and its
      version number]", the statement "The Open Data is made available to the public under the
      Open Government Data License, User can make use of it when complying to the condition and
      obligation of its terms.", and the license's address. The page in Chinese shows the
      Chinese one, word for word as the annex has it.
    - The Taiwan Stock Exchange's OpenAPI (`openapi.twse.com.tw/v1/swagger.json`, `info`) welcomes
      programs and links that license. The Taipei Exchange's OpenAPI links its terms, which forbid
      automated download other than in a way it agrees to, ask that a quote names its source
      (section 7), and except the data it gives the open data platform. On the platform, two of
      the four tables read were found, both under license code 1: the listed stocks' daily
      trading (`data.gov.tw/api/v2/rest/dataset/11549`) and the OTC ex-dividend notices
      (`/11634`). The OTC quotes table was not found there (the platform's search page is drawn
      by script and gave no result to a program); the listed ex-dividend notices were not looked
      up, as the Taiwan Stock Exchange's OpenAPI as a whole links the license.
    - The data's names and versions are the OpenAPIs' own (`summary` of each path; `info.version`
      1.0 and 1.0.0). The year is the year the page is shown.
    - FinMind's terms say nothing of attribution; its Commercial Use page asks to credit the source
      as "FinMind", and its Disclaimer (section 2) asks that the original providing agency be named
      too. The service is not a commercial use; FinMind is named with the two exchanges anyway.
