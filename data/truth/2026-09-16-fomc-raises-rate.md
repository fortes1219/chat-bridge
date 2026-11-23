---
title: 聯準會9月升息（1/4 percentage point），美股收低
event_date: 2026-09-16
targets: [2, 1]
markets: [US]
tickers: [NVDA, AMD]
exposure: [fed_policy, us_equity_broad, rates_treasuries]
significance: key
keyword_groups:
  - [聯準會, Fed, Federal Reserve]
  - [FOMC, 聯邦公開市場委員會]
  - [升息, rate hike, raise the target range]
  - [華許, Warsh, Kevin Warsh]
  - [聯準會主席, Fed Chairman]
  - [通膨, inflation]
  - [公債殖利率, Treasury yield]
  - [10-year Treasury]
  - [two-year Treasury]
  - [標普500, S&P 500]
  - [道瓊, Dow Jones Industrial Average]
  - [那斯達克, Nasdaq composite]
sources:
  - id: s1
    url: https://www.federalreserve.gov/newsevents/pressreleases/monetary20260916a.htm
    publisher: Board of Governors of the Federal Reserve System
    published: 2026-09-16
    accessed: 2026-11-18
    lang: en
    format: html
  - id: s2
    url: https://www.pbs.org/newshour/economy/u-s-stocks-slip-after-the-fed-raises-interest-rate-hints-more-hikes-may-be-on-the-way
    publisher: PBS NewsHour（Associated Press，Stan Choe）
    published: 2026-09-16
    accessed: 2026-11-18
    lang: en
    format: html
  - id: d1
    url: https://query1.finance.yahoo.com/v8/finance/chart/
    publisher: Yahoo Finance chart API（程式下載的日線收盤；^TWII、2330.TW、2308.TW、0050.TW、006208.TW、^GSPC、^IXIC、^DJI、^SOX）
    published: unknown
    accessed: 2026-11-18T03:23:58+00:00
    lang: en
    format: json
---

## 事件發生

- The Committee decided "to raise the target range for the federal funds rate by 1/4 percentage point to 3-3/4 to 4 percent". [s1]
- The statement was approved "by a 12 – 0 vote". [s1]
- The statement said: "Inflation remains elevated. Today's policy action will support a timelier return to the Committee's 2 percent goal". [s1]
- The statement said: "Economic activity is expanding at a solid pace. While uncertainty remains elevated owing, in part, to geopolitical developments, domestic spending has been resilient". [s1]

## 影響股市證據

- AP reported that stock prices weakened later in the day as Fed Chairman Kevin Warsh said repeatedly in a press conference that inflation remains too high. [s2]
- Warsh, as quoted by AP: "The plain fact is that inflation is too high and has been for too long". [s2]
- "All told, the S&P 500 fell 33.92 points to 7,551.81". [s2]
- "The Dow Jones Industrial Average dropped 631.21 to 51,461.90, and the Nasdaq composite slipped 3.15 to 25,978.42". [s2]

## 相關標的

- The two-year Treasury yield "jumped to 4.74% from 4.67% late Tuesday"; the 10-year yield ticked up "to 5.01% from 5.00% late Tuesday". [s2]
- On the same day, "Nvidia rose 0.8%, and Advanced Micro Devices climbed 1.6%" … [s2]

## 當日與之後的行情

> 由程式依日線收盤價計算（資料來源 d1；收盤未調整除息），不是新聞來源的話。事件市場：US；美股序列對準 event_date，台股序列對準 event_date 隔天，D0 是對準日當天或之後的第一個交易日。盤後才公布的事件，當日欄反應不到，請看次一交易日欄。

| 序列 | 對準日 | 前一交易日 | 前一交易日收盤 | 前一交易日漲跌% | D0 | D0 收盤 | 當日% | 次一交易日% | D+5 累計%（相對前一交易日收盤） | 註 |
|---|---|---|---|---|---|---|---|---|---|---|
| 加權指數 | 2026-09-17 | 2026-09-16 | 45848.90 | +0.74% | 2026-09-17 | 46288.00 | +0.96% | +1.93% | +4.75% |  |
| 台積電 2330 | 2026-09-17 | 2026-09-16 | 2380.00 | -0.21% | 2026-09-17 | 2425.00 | +1.89% | +1.44% | +3.99% | 視窗內有除息日 2026-09-16（收盤未調整） |
| 台達電 2308 | 2026-09-17 | 2026-09-16 | 1710.00 | +2.40% | 2026-09-17 | 1685.00 | -1.46% | +2.97% | +11.70% |  |
| 元大台灣50 0050 | 2026-09-17 | 2026-09-16 | 106.90 | +0.61% | 2026-09-17 | 108.05 | +1.08% | +1.67% | +5.14% |  |
| 富邦台50 006208 | 2026-09-17 | 2026-09-16 | 244.60 | +0.45% | 2026-09-17 | 247.40 | +1.14% | +1.54% | +5.01% |  |
| S&P 500 | 2026-09-16 | 2026-09-15 | 7585.73 | -0.45% | 2026-09-16 | 7551.81 | -0.45% | +1.14% | +1.59% |  |
| Nasdaq Composite | 2026-09-16 | 2026-09-15 | 25981.57 | -0.78% | 2026-09-16 | 25978.43 | -0.01% | +1.69% | +3.67% |  |
| Dow Jones Industrial Average | 2026-09-16 | 2026-09-15 | 52093.11 | -0.63% | 2026-09-16 | 51461.90 | -1.21% | +0.61% | -1.12% |  |
| 費城半導體指數 | 2026-09-16 | 2026-09-15 | 11175.55 | +0.40% | 2026-09-16 | 11246.11 | +0.63% | +3.14% | +12.16% |  |

> significance 依據（key）：這段期間唯一一次升息決策，改變利率路徑。
