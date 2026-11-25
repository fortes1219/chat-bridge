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
