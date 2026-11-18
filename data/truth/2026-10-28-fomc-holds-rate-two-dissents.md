---
title: 聯準會10月維持利率不變、兩位委員主張升息，美股三大指數上漲
event_date: 2026-10-28
targets: [2, 1]
markets: [US]
tickers: []
exposure: [fed_policy, us_equity_broad, rates_treasuries]
significance: supporting
keyword_groups:
  - [聯準會, Fed, Federal Reserve, FOMC, 聯邦公開市場委員會]
  - [聯邦基金利率, federal funds rate, 利率決策, 按兵不動]
  - [反對票, dissent, 升息派, Cook, Hammack]
  - [通膨, inflation]
  - [標普500, S&P 500, 道瓊, Dow, 那斯達克, Nasdaq]
sources:
  - id: s1
    url: https://www.federalreserve.gov/newsevents/pressreleases/monetary20261028a.htm
    publisher: Board of Governors of the Federal Reserve System
    published: 2026-10-28
    accessed: 2026-11-18
    lang: en
    format: html
  - id: s2
    url: https://www.krmg.com/2026/10/28/how-major-us-stock-indexes-fared-wednesday-10-28-2026/
    publisher: 96.5 KRMG（Associated Press）
    published: 2026-10-28
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

- The Committee decided "to maintain the target range for the federal funds rate at 3-3/4 to 4 percent". [s1]
- The statement was approved "by a 10 – 2 vote". [s1]
- "Voting against the monetary policy action were Lisa D. Cook and Beth M. Hammack, who preferred to raise the target range for the federal funds rate by 1/4 percentage point at this meeting". [s1]
- The statement said: "Inflation remains elevated. The accumulation of more information will help the Committee determine the policy stance appropriate to ensure a timely return of inflation to the Committee's 2 percent goal". [s1]
- The statement said: "Economic activity is expanding at a strong pace". [s1]

## 影響股市證據

- AP: the S&P 500 rose 21.38 to 7,743.98 (0.3%); the Dow rose 97.53 to 52,475.10 (0.2%); the Nasdaq rose 72.04 to 26,549.85 (0.3%). [s2]
- AP reported the Fed decided not to raise its main interest rate. [s2]

## 相關標的

- AP: the two-year Treasury yield initially jumped, then reversed as traders pared expectations for coming hikes. [s2]

## 當日與之後的行情

> 由程式依日線收盤價計算（資料來源 d1；收盤未調整除息），不是新聞來源的話。事件市場：US；美股序列對準 event_date，台股序列對準 event_date 隔天，D0 是對準日當天或之後的第一個交易日。盤後才公布的事件，當日欄反應不到，請看次一交易日欄。

| 序列 | 對準日 | 前一交易日 | 前一交易日收盤 | 前一交易日漲跌% | D0 | D0 收盤 | 當日% | 次一交易日% | D+5 累計%（相對前一交易日收盤） | 註 |
|---|---|---|---|---|---|---|---|---|---|---|
| 加權指數 | 2026-10-29 | 2026-10-28 | 47035.58 | +2.04% | 2026-10-29 | 46368.33 | -1.42% | -2.49% | -11.61% |  |
| 台積電 2330 | 2026-10-29 | 2026-10-28 | 2425.00 | +1.04% | 2026-10-29 | 2415.00 | -0.41% | -1.86% | -7.63% |  |
| 台達電 2308 | 2026-10-29 | 2026-10-28 | 1550.00 | +2.65% | 2026-10-29 | 1480.00 | -4.52% | -9.80% | -27.10% |  |
| 元大台灣50 0050 | 2026-10-29 | 2026-10-28 | 108.65 | +1.92% | 2026-10-29 | 107.25 | -1.29% | -2.14% | -10.58% |  |
| 富邦台50 006208 | 2026-10-29 | 2026-10-28 | 249.05 | +1.82% | 2026-10-29 | 245.75 | -1.33% | -2.03% | -10.64% |  |
| S&P 500 | 2026-10-28 | 2026-10-27 | 7722.60 | +0.60% | 2026-10-28 | 7743.98 | +0.28% | -0.30% | -0.44% |  |
| Nasdaq Composite | 2026-10-28 | 2026-10-27 | 26477.81 | +1.18% | 2026-10-28 | 26549.85 | +0.27% | -1.38% | -2.80% |  |
| Dow Jones Industrial Average | 2026-10-28 | 2026-10-27 | 52377.57 | +0.03% | 2026-10-28 | 52475.10 | +0.19% | -0.25% | +1.87% |  |
| 費城半導體指數 | 2026-10-28 | 2026-10-27 | 11482.50 | +3.60% | 2026-10-28 | 11684.00 | +1.75% | -1.42% | -10.57% |  |

> significance 依據（supporting）：聯準會開會日，來源記載美股上漲，是「聯準會決策沒有造成動盪」的佐證。
