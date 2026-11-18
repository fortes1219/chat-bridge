---
title: 聯準會6月維持利率不變，經濟預測公布後美股下跌
event_date: 2026-06-17
targets: [2, 1]
markets: [US]
tickers: [MSFT, AMZN, NVDA]
exposure: [fed_policy, us_equity_broad, rates_treasuries]
significance: key
keyword_groups:
  - [聯準會, Fed, Federal Reserve, FOMC, 聯邦公開市場委員會]
  - [聯邦基金利率, federal funds rate, 利率決策, 按兵不動]
  - [經濟預測, 點陣圖, projections]
  - [升息, rate hike, increase]
  - [華許, Warsh, Kevin Warsh, 聯準會主席]
  - [通膨, inflation, PCE]
  - [中東衝突, conflict in the Middle East]
  - [公債殖利率, Treasury yield]
  - [標普500, S&P 500, 道瓊, Dow, 那斯達克, Nasdaq]
sources:
  - id: s1
    url: https://www.federalreserve.gov/newsevents/pressreleases/monetary20260617a.htm
    publisher: Board of Governors of the Federal Reserve System
    published: 2026-06-17
    accessed: 2026-11-18
    lang: en
    format: html
  - id: s2
    url: https://www.adn.com/business-economy/2026/06/17/us-stocks-sink-on-worries-about-a-possible-hike-to-interest-rates-this-year-by-the-fed/
    publisher: Anchorage Daily News（Associated Press，Stan Choe）
    published: 2026-06-17
    accessed: 2026-11-18
    lang: en
    format: html
  - id: s3
    url: https://www.federalreserve.gov/monetarypolicy/fomcprojtabl20260617.htm
    publisher: Board of Governors of the Federal Reserve System
    published: 2026-06-17
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

- The Committee decided "to maintain the target range for the federal funds rate at 3-1/2 to 3-3/4 percent". [s1]
- The statement was approved "by a 12 – 0 vote". [s1]
- The statement said: "Inflation remains elevated relative to the Committee's 2 percent goal, in part reflecting supply shocks that have driven price increases in certain sectors, including energy". [s1]
- The statement said: "Economic activity is expanding at a solid pace despite elevated uncertainty that owes, in part, to the conflict in the Middle East". [s1]
- In the June projections table, the median projection for the federal funds rate is 3.8 for 2026, 3.6 for 2027, 3.4 for 2028 and 3.1 for the longer run; the 2026 median for PCE inflation is 3.6. [s3]

## 影響股市證據

- AP: the S&P 500 dropped 1.2%, falling 91.25 points to 7,420.10; the Dow fell 507.12 to 51,492.55; the Nasdaq sank 354.69 to 26,021.66 (1.3%). [s2]
- AP tied the drop to the Fed's projections showing "nine of 18" policymakers foresee at least one rate increase this year. [s2]
- AP cited CME data showing an 84% probability of a hike this year, up from 59.5%. [s2]

## 相關標的

- AP: the 10-year Treasury yield rose to 4.49% from 4.43%, and the 2-year yield jumped to 4.21% from 4.05%. [s2]
- AP: Microsoft fell 3.8%, Amazon 3.5% and Nvidia 1.3%; Brent crude rose 0.7% to $79.55. [s2]

## 當日與之後的行情

> 由程式依日線收盤價計算（資料來源 d1；收盤未調整除息），不是新聞來源的話。事件市場：US；美股序列對準 event_date，台股序列對準 event_date 隔天，D0 是對準日當天或之後的第一個交易日。盤後才公布的事件，當日欄反應不到，請看次一交易日欄。

| 序列 | 對準日 | 前一交易日 | 前一交易日收盤 | 前一交易日漲跌% | D0 | D0 收盤 | 當日% | 次一交易日% | D+5 累計%（相對前一交易日收盤） | 註 |
|---|---|---|---|---|---|---|---|---|---|---|
| 加權指數 | 2026-06-18 | 2026-06-17 | 45877.39 | +0.15% | 2026-06-18 | 46465.20 | +1.28% | +2.75% | -2.85% |  |
| 台積電 2330 | 2026-06-18 | 2026-06-17 | 2385.00 | -0.62% | 2026-06-18 | 2410.00 | +1.05% | +4.15% | -1.89% |  |
| 台達電 2308 | 2026-06-18 | 2026-06-17 | 2155.00 | -3.36% | 2026-06-18 | 2150.00 | -0.23% | +0.00% | -16.01% | 視窗內有除息日 2026-06-17（收盤未調整） |
| 元大台灣50 0050 | 2026-06-18 | 2026-06-17 | 106.00 | +0.09% | 2026-06-18 | 107.30 | +1.23% | +3.59% | -2.74% |  |
| 富邦台50 006208 | 2026-06-18 | 2026-06-17 | 246.30 | +0.39% | 2026-06-18 | 249.10 | +1.14% | +3.35% | -3.09% |  |
| S&P 500 | 2026-06-17 | 2026-06-16 | 7511.35 | -0.57% | 2026-06-17 | 7420.10 | -1.21% | +1.08% | -2.05% |  |
| Nasdaq Composite | 2026-06-17 | 2026-06-16 | 26376.34 | -1.15% | 2026-06-17 | 26021.66 | -1.34% | +1.91% | -3.86% |  |
| Dow Jones Industrial Average | 2026-06-17 | 2026-06-16 | 51999.67 | +0.64% | 2026-06-17 | 51492.55 | -0.98% | +0.14% | -0.15% |  |
| 費城半導體指數 | 2026-06-17 | 2026-06-16 | 13294.22 | -5.71% | 2026-06-17 | 13477.07 | +1.38% | +6.42% | +4.86% |  |

## 後續與不同說法

- Fed Chairman Kevin Warsh, as reported by AP, said he "didn't hear tons of conviction" behind the projections and did not give a year-end rate forecast. [s2]

> significance 依據（key）：改變利率路徑預期的決策，來源把當天美股下跌直接歸因於聯準會的預測，是這段期間聯準會最明確造成下跌的一次。
